"""
Migration: Halloween Adventure Seed

Seeds the database with a short Halloween-themed adventure for testing.
This adventure features 5 locations: Church, Graveyard (with a dead end), and Crypt.
"""

from datetime import datetime
from tinydb import TinyDB


def up(db: TinyDB):
    """Seed the Halloween adventure."""
    adventures_table = db.table('adventures')

    # Define the Halloween Adventure
    halloween_adventure = {
        "id": "halloween_2025",
        "name": "The Midnight Vigil",
        "description": "A short Halloween adventure. The old church bell tolls midnight as you prepare for your vigil. Strange sounds echo from the graveyard beyond...",
        "author": "Zaik Team",
        "version": "1.0.0",
        "created_at": datetime.now().isoformat(),
        "updated_at": datetime.now().isoformat(),
        "starting_location_id": "church",
        "difficulty": "easy",
        "estimated_duration": 15,
        "tags": ["halloween", "horror", "short", "atmospheric"],

        # Location Graph
        "locations": {
            # Starting Location
            "church": {
                "id": "church",
                "name": "St. Margaret's Church",
                "description": "You stand in the dimly lit nave of St. Margaret's, an old stone church that has watched over this village for centuries. Rows of weathered wooden pews face a simple altar, where flickering candles cast dancing shadows on the walls. The air smells of old incense and damp stone. A heavy wooden door leads out to the graveyard to the north, while a narrow passage descends into darkness to the west.",
                "mood": "solemn",
                "tags": ["indoor", "safe"],
                "exits": {
                    "north": {
                        "direction": "north",
                        "location_id": "graveyard",
                        "description": "A heavy oak door leading to the graveyard"
                    },
                    "west": {
                        "direction": "west",
                        "location_id": "bell_tower_stairs",
                        "description": "A narrow stone stairway spiraling upward into the bell tower"
                    }
                },
                "items": [
                    {
                        "id": "candle",
                        "name": "blessed candle",
                        "description": "A white candle that burns with a steady, pure flame. It feels warm to the touch and seems to push back the shadows.",
                        "takeable": True,
                        "visible": True
                    },
                    {
                        "id": "hymnal",
                        "name": "old hymnal",
                        "description": "A leather-bound hymnal, its pages yellowed with age. Some pages seem to have been marked.",
                        "takeable": True,
                        "visible": True
                    }
                ]
            },

            # Dead End - Bell Tower
            "bell_tower_stairs": {
                "id": "bell_tower_stairs",
                "name": "Bell Tower Stairs",
                "description": "You climb the narrow spiral staircase, your footsteps echoing off the cold stone walls. Cobwebs brush your face as you ascend. The stairs end at a locked wooden trapdoor above - it hasn't been opened in years, judging by the rust on the hinges. The bell rope that once hung here has long since rotted away.",
                "mood": "claustrophobic",
                "tags": ["indoor", "dead_end"],
                "exits": {
                    "east": {
                        "direction": "east",
                        "location_id": "church",
                        "description": "Back down the stairs to the church"
                    }
                },
                "items": []
            },

            # Main Path - Graveyard
            "graveyard": {
                "id": "graveyard",
                "name": "Church Graveyard",
                "description": "The graveyard stretches out before you, a forest of weathered headstones and Celtic crosses half-hidden by overgrown grass and creeping ivy. A pale moon casts silver light over the ancient graves, creating pools of shadow between the monuments. The wind whispers through the yew trees, carrying with it the faint scent of turned earth. To the south, you can return to the safety of the church. A mausoleum stands to the north, its iron gate hanging open.",
                "mood": "eerie",
                "tags": ["outdoor", "atmospheric"],
                "exits": {
                    "south": {
                        "direction": "south",
                        "location_id": "church",
                        "description": "Back to the church"
                    },
                    "north": {
                        "direction": "north",
                        "location_id": "mausoleum",
                        "description": "An old stone mausoleum with an open iron gate"
                    }
                },
                "items": [
                    {
                        "id": "flowers",
                        "name": "wilted flowers",
                        "description": "A small bouquet of flowers, recently placed on one of the graves. They've already begun to wilt in the cold night air.",
                        "takeable": True,
                        "visible": True
                    }
                ]
            },

            # Path to Crypt
            "mausoleum": {
                "id": "mausoleum",
                "name": "Blackwood Mausoleum",
                "description": "You enter the Blackwood family mausoleum, a small stone chamber barely larger than a closet. The air is thick with the smell of decay and centuries-old dust. Stone shelves line the walls, holding the remains of the Blackwood family, their names barely legible on tarnished brass plates. In the floor, partially hidden by fallen leaves and debris, you notice an iron ring set into a stone trapdoor. The graveyard lies to the south.",
                "mood": "oppressive",
                "tags": ["indoor", "dark"],
                "exits": {
                    "south": {
                        "direction": "south",
                        "location_id": "graveyard",
                        "description": "Back to the graveyard"
                    },
                    "down": {
                        "direction": "down",
                        "location_id": "crypt",
                        "description": "A stone trapdoor with an iron ring, leading down into darkness"
                    }
                },
                "items": [
                    {
                        "id": "brass_plate",
                        "name": "brass memorial plate",
                        "description": "A tarnished brass plate that has fallen from one of the shelves. It reads: 'Lord Edmund Blackwood, 1803-1847. May he find the peace in death that eluded him in life.'",
                        "takeable": True,
                        "visible": True
                    }
                ]
            },

            # Final Location - Crypt
            "crypt": {
                "id": "crypt",
                "name": "The Forgotten Crypt",
                "description": "You descend into a vast underground crypt that shouldn't exist beneath the small mausoleum. The ceiling arches high above, supported by ancient stone pillars carved with symbols you don't recognize. Rows of stone sarcophagi line the chamber, their lids askew or missing entirely. In the center of the room stands an altar of black stone, covered in melted candle wax and strange markings. The air is freezing cold, and your breath mists before you. \n\nAs you stand there, you hear it - a slow, rhythmic sound echoing through the chamber. Footsteps. Something is approaching from the darkness beyond...\n\nYour adventure continues, but this is where our story ends for now.",
                "mood": "terrifying",
                "tags": ["indoor", "dark", "climax"],
                "exits": {
                    "up": {
                        "direction": "up",
                        "location_id": "mausoleum",
                        "description": "Back up to the mausoleum"
                    }
                },
                "items": [
                    {
                        "id": "ancient_key",
                        "name": "ancient silver key",
                        "description": "An ornate silver key, its metal still bright despite the centuries. Its bow is shaped like a skull, and strange runes are etched along its length. You're certain this key opens something important, but what?",
                        "takeable": True,
                        "visible": True
                    },
                    {
                        "id": "altar",
                        "name": "black stone altar",
                        "description": "An altar of polished black stone, carved with symbols that seem to shift and writhe when you look directly at them. The surface is covered in layers of melted candle wax.",
                        "takeable": False,
                        "visible": True
                    }
                ]
            }
        }
    }

    # Insert the adventure (or update if it exists)
    from tinydb import Query
    Adventure = Query()
    adventures_table.upsert(halloween_adventure, Adventure.id == "halloween_2025")

    print(f"✓ Seeded Halloween adventure: {halloween_adventure['name']}")
