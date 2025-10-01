#!/usr/bin/env python3
"""
Test Python project for code-graph-mCP validation.
Simple project with multiple modules and functions to test analysis capabilities.
"""

import json
from typing import List, Dict, Optional
from dataclasses import dataclass


@dataclass
class User:
    """Simple user data class."""
    id: int
    name: str
    email: str
    
    def to_dict(self) -> Dict:
        """Convert user to dictionary."""
        return {
            'id': self.id,
            'name': self.name,
            'email': self.email
        }


class UserManager:
    """Manages user operations."""
    
    def __init__(self):
        self.users: List[User] = []
        self.next_id = 1
    
    def add_user(self, name: str, email: str) -> User:
        """Add a new user."""
        user = User(id=self.next_id, name=name, email=email)
        self.users.append(user)
        self.next_id += 1
        return user
    
    def get_user(self, user_id: int) -> Optional[User]:
        """Get user by ID."""
        for user in self.users:
            if user.id == user_id:
                return user
        return None
    
    def get_all_users(self) -> List[User]:
        """Get all users."""
        return self.users.copy()
    
    def delete_user(self, user_id: int) -> bool:
        """Delete user by ID."""
        for i, user in enumerate(self.users):
            if user.id == user_id:
                del self.users[i]
                return True
        return False


def calculate_user_stats(users: List[User]) -> Dict:
    """Calculate statistics for users."""
    if not users:
        return {'total': 0, 'avg_name_length': 0}
    
    total = len(users)
    name_lengths = [len(user.name) for user in users]
    avg_name_length = sum(name_lengths) / total
    
    return {
        'total': total,
        'avg_name_length': avg_name_length,
        'name_lengths': name_lengths
    }


def main():
    """Main function demonstrating usage."""
    manager = UserManager()
    
    # Add some users
    manager.add_user("Alice", "alice@example.com")
    manager.add_user("Bob", "bob@example.com")
    manager.add_user("Charlie", "charlie@example.com")
    
    # Get statistics
    users = manager.get_all_users()
    stats = calculate_user_stats(users)
    
    # Print results
    print(f"Total users: {stats['total']}")
    print(f"Average name length: {stats['avg_name_length']:.2f}")
    
    # Export to JSON
    user_dicts = [user.to_dict() for user in users]
    with open('users.json', 'w') as f:
        json.dump(user_dicts, f, indent=2)
    
    print("User data exported to users.json")


if __name__ == "__main__":
    main()