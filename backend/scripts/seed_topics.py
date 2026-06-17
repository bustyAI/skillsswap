#!/usr/bin/env python
"""Seed script for initial topic catalog.

Creates ~30 topics across four categories:
- Programming (10 topics)
- Design (6 topics)
- Business (8 topics)
- Languages (6 topics)

Usage:
    cd backend
    uv run python scripts/seed_topics.py

This script is idempotent - running it multiple times will not create
duplicate topics (uses ON CONFLICT DO NOTHING).

Note: This does NOT generate embeddings. Embeddings are generated in Phase 5
when the recommender module is built.
"""

import asyncio
import os
import sys
from uuid import UUID

# Add the backend app to the path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine

# Topic catalog organized by category
# Each category is a parent topic, with child topics beneath it
TOPIC_CATALOG: dict[str, dict[str, str | None]] = {
    "Programming": {
        "Python": "General-purpose programming language known for readability and versatility",
        "JavaScript": "Dynamic language for web development, both frontend and backend",
        "TypeScript": "Typed superset of JavaScript for large-scale applications",
        "Go": "Statically typed, compiled language designed for simplicity and efficiency",
        "Rust": "Systems programming language focused on safety and performance",
        "Java": "Object-oriented language widely used in enterprise applications",
        "C++": "High-performance language for systems, games, and embedded software",
        "Ruby": "Dynamic language known for elegant syntax and Rails framework",
        "Swift": "Modern language for iOS, macOS, and Apple platform development",
        "Kotlin": "Modern JVM language, official for Android development",
    },
    "Design": {
        "UI Design": "Creating visual interfaces for digital products",
        "UX Design": "Designing user experiences and interaction flows",
        "Graphic Design": "Visual communication through typography, imagery, and color",
        "Figma": "Collaborative interface design tool",
        "Adobe Creative Suite": "Industry-standard tools for design and creative work",
        "Product Design": "End-to-end design of digital products from concept to launch",
    },
    "Business": {
        "Marketing": "Strategies for promoting products and building brand awareness",
        "Finance": "Financial planning, analysis, and management",
        "Leadership": "Skills for leading teams and organizations effectively",
        "Entrepreneurship": "Starting and growing new business ventures",
        "Project Management": "Planning, executing, and delivering projects successfully",
        "Data Analysis": "Extracting insights from data to inform decisions",
        "Public Speaking": "Presenting ideas effectively to audiences",
        "Career Development": "Building and advancing your professional career",
    },
    "Languages": {
        "Spanish": "Second most spoken native language in the world",
        "French": "Romance language spoken across five continents",
        "Mandarin Chinese": "Most spoken language by number of native speakers",
        "German": "Widely spoken in Central Europe, key for business and engineering",
        "Japanese": "Language of Japan, important for technology and culture",
        "Portuguese": "Spoken in Brazil, Portugal, and several African nations",
    },
}


async def seed_topics(database_url: str) -> None:
    """Insert topics into the database.

    Args:
        database_url: PostgreSQL connection string (async format)
    """
    engine = create_async_engine(database_url, echo=False)

    async with engine.begin() as conn:
        # First, insert parent categories
        parent_ids: dict[str, UUID] = {}

        for category_name in TOPIC_CATALOG:
            # Use raw SQL with ON CONFLICT to handle idempotency
            result = await conn.execute(
                text(
                    """
                    INSERT INTO topic (name, description, parent_topic_id)
                    VALUES (:name, :description, NULL)
                    ON CONFLICT (name) DO UPDATE SET name = EXCLUDED.name
                    RETURNING id
                    """
                ),
                {
                    "name": category_name,
                    "description": f"Topics related to {category_name.lower()}",
                },
            )
            row = result.fetchone()
            if row:
                parent_ids[category_name] = row[0]
                print(f"Category: {category_name} (id: {row[0]})")

        # Then, insert child topics
        for category_name, topics in TOPIC_CATALOG.items():
            parent_id = parent_ids.get(category_name)
            for topic_name, description in topics.items():
                result = await conn.execute(
                    text(
                        """
                        INSERT INTO topic (name, description, parent_topic_id)
                        VALUES (:name, :description, :parent_id)
                        ON CONFLICT (name) DO UPDATE SET name = EXCLUDED.name
                        RETURNING id
                        """
                    ),
                    {
                        "name": topic_name,
                        "description": description,
                        "parent_id": parent_id,
                    },
                )
                row = result.fetchone()
                if row:
                    print(f"  - {topic_name} (id: {row[0]})")

    await engine.dispose()
    print(
        f"\nSeeded {4 + sum(len(t) for t in TOPIC_CATALOG.values())} topics successfully."
    )


async def main() -> None:
    """Main entry point."""
    # Get database URL from environment or use default
    database_url = os.environ.get(
        "DATABASE_URL",
        "postgresql+asyncpg://skillswap:skillswap_dev_123@localhost:5432/skillswap",
    )

    # Ensure it's an async URL
    if database_url.startswith("postgresql://"):
        database_url = database_url.replace("postgresql://", "postgresql+asyncpg://", 1)

    print("Connecting to database...")
    print(f"URL: {database_url.split('@')[1] if '@' in database_url else 'localhost'}")
    print()

    await seed_topics(database_url)


if __name__ == "__main__":
    asyncio.run(main())
