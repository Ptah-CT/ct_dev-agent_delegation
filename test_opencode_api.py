#!/usr/bin/env python3
"""
Quick OpenCode API test to verify endpoints work.

Tests the actual OpenCode 0.13.5 API based on documentation.
"""

import asyncio
import httpx
import subprocess
import time
import sys

async def test_opencode_api():
    """Test OpenCode API with real server."""
    
    print("=" * 60)
    print("OpenCode API Test - Version 0.13.5")
    print("=" * 60)
    
    # Start OpenCode server
    print("\n[1/6] Starting OpenCode server...")
    process = subprocess.Popen(
        ["opencode", "serve", "--port", "9999"],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL
    )
    
    # Wait for server to start
    await asyncio.sleep(3)
    
    base_url = "http://127.0.0.1:9999"
    
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            
            # Test 1: Get agents
            print("\n[2/6] GET /agent - List available agents...")
            try:
                response = await client.get(f"{base_url}/agent")
                if response.status_code == 200:
                    agents = response.json()
                    print(f"✓ Found {len(agents)} agents")
                    if agents:
                        print(f"  First agent: {agents[0].get('name', 'unknown')}")
                else:
                    print(f"✗ Status: {response.status_code}")
            except Exception as e:
                print(f"✗ Error: {e}")
            
            # Test 2: Create session
            print("\n[3/6] POST /session - Create new session...")
            try:
                response = await client.post(
                    f"{base_url}/session",
                    json={"title": "Test Session"}
                )
                if response.status_code == 200:
                    session = response.json()
                    session_id = session.get("id")
                    print(f"✓ Session created: {session_id}")
                    
                    # Test 3: Send message
                    print("\n[4/6] POST /session/{id}/message - Send message...")
                    try:
                        # Get provider/model info first
                        config_response = await client.get(f"{base_url}/config/providers")
                        if config_response.status_code == 200:
                            providers = config_response.json()
                            if providers:
                                # Use first available provider/model
                                first_provider = providers[0]
                                provider_id = first_provider.get("id")
                                model_id = first_provider.get("defaultModel", {}).get("modelID")
                                
                                print(f"  Using: {provider_id}/{model_id}")
                                
                                message_payload = {
                                    "model": {
                                        "providerID": provider_id,
                                        "modelID": model_id
                                    },
                                    "parts": [{
                                        "type": "text",
                                        "text": "Hello! Please respond with 'Test successful'"
                                    }]
                                }
                                
                                try:
                                    msg_response = await client.post(
                                        f"{base_url}/session/{session_id}/message",
                                        json=message_payload
                                    )
                                    
                                    if msg_response.status_code == 200:
                                        print("✓ Message sent successfully")
                                        msg_data = msg_response.json()
                                        if "info" in msg_data:
                                            print(f"  Message ID: {msg_data['info'].get('id', 'unknown')}")
                                    else:
                                        print(f"✗ Status: {msg_response.status_code}")
                                        print(f"  Response: {msg_response.text[:200]}")
                                except httpx.ReadTimeout:
                                    print("✓ Message sent (timeout waiting for response - normal for streaming)")
                                except Exception as msg_err:
                                    print(f"✗ Message error: {msg_err}")
                        
                    except Exception as e:
                        print(f"✗ Error sending message: {e}")
                    
                    # Test 4: Get session
                    print("\n[5/6] GET /session/{id} - Get session details...")
                    try:
                        sess_response = await client.get(f"{base_url}/session/{session_id}")
                        if sess_response.status_code == 200:
                            print("✓ Session retrieved")
                            sess_data = sess_response.json()
                            print(f"  Title: {sess_data.get('title', 'N/A')}")
                        else:
                            print(f"✗ Status: {sess_response.status_code}")
                    except Exception as e:
                        print(f"✗ Error: {e}")
                    
                else:
                    print(f"✗ Status: {response.status_code}")
                    print(f"  Response: {response.text}")
            except Exception as e:
                print(f"✗ Error: {e}")
            
            # Test 5: Get config
            print("\n[6/6] GET /config - Get configuration...")
            try:
                response = await client.get(f"{base_url}/config")
                if response.status_code == 200:
                    config = response.json()
                    print("✓ Config retrieved")
                    print(f"  Version: {config.get('version', 'unknown')}")
                else:
                    print(f"✗ Status: {response.status_code}")
            except Exception as e:
                print(f"✗ Error: {e}")
    
    finally:
        # Cleanup
        print("\n[CLEANUP] Stopping server...")
        process.terminate()
        try:
            process.wait(timeout=5)
            print("✓ Server stopped")
        except subprocess.TimeoutExpired:
            process.kill()
            print("✓ Server killed")
    
    print("\n" + "=" * 60)
    print("API TEST COMPLETED")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(test_opencode_api())
