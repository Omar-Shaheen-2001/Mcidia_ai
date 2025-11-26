#!/usr/bin/env python3
"""Script to create seed documents in the knowledge base"""
import os
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../..'))

from app import create_app, db
from models import Document
from datetime import datetime

def create_seed_documents():
    app = create_app()
    with app.app_context():
        # Check if Business Fundamentals already exists
        existing = db.session.query(Document).filter_by(
            filename='Business Fundamentals - Complete Guide'
        ).first()
        
        if existing:
            print("✓ Business Fundamentals document already exists")
            return
        
        # Read the markdown file
        md_file = Path(__file__).parent / 'business-fundamentals-ar.md'
        if not md_file.exists():
            print(f"✗ File not found: {md_file}")
            return
        
        with open(md_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Create document record
        doc = Document(
            filename='Business Fundamentals - Complete Guide',
            file_type='md',
            file_path=str(md_file),
            content_text=content[:50000],
            user_id=1,  # Admin
            embeddings='{"category": "Business Fundamentals", "tags": ["fundamentals", "strategy", "models"], "quality_score": 95}'
        )
        
        db.session.add(doc)
        db.session.commit()
        
        print(f"✓ Created seed document: Business Fundamentals (ID: {doc.id})")

if __name__ == '__main__':
    create_seed_documents()
