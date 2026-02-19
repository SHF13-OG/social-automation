"""Generate sample overlay PNGs for visual review of the hook-based layout."""

from pathlib import Path

from src.media.text_overlay import generate_single_overlay

SAMPLES_DIR = Path("media/samples")

SAMPLES = [
    {
        "name": "sample_wedding",
        "hook_text": "Is your child getting married soon?",
        "verse_ref": "Jeremiah 29:11",
        "verse_text": (
            "For I know the plans I have for you, declares the Lord, "
            "plans for welfare and not for evil, to give you a future and a hope."
        ),
        "prayer_text": (
            "Heavenly Father, we come before You today with hearts full of joy "
            "and anticipation. As our children step into this sacred covenant of "
            "marriage, we ask for Your blessing to rest upon them. Guide their "
            "steps as they build a life together, rooted in Your love."
        ),
        "theme_slug": "wedding-joy",
    },
    {
        "name": "sample_money",
        "hook_text": "Are you feeling worried about money?",
        "verse_ref": "Philippians 4:19",
        "verse_text": (
            "And my God will supply every need of yours according to "
            "his riches in glory in Christ Jesus."
        ),
        "prayer_text": (
            "Lord, You know the weight we carry when the bills stack up "
            "and the numbers don't add up. We lay our financial fears at "
            "Your feet today. Remind us that You are our provider, and "
            "that no need is too great for Your abundant grace."
        ),
        "theme_slug": "money-worry",
    },
    {
        "name": "sample_purity",
        "hook_text": "Is what you're watching pulling you from God?",
        "verse_ref": "Romans 12:2",
        "verse_text": (
            "Do not be conformed to this world, but be transformed by the "
            "renewal of your mind, that by testing you may discern what is "
            "the will of God, what is good and acceptable and perfect."
        ),
        "prayer_text": (
            "Father, we confess that the world's images and distractions "
            "pull at our hearts. Give us the strength to turn away from "
            "what dims Your light in us. Renew our minds and guard our "
            "eyes, that we may see only what honors You."
        ),
        "theme_slug": "purity-struggle",
    },
    {
        "name": "sample_lonely",
        "hook_text": "Are you feeling lonely even around others?",
        "verse_ref": "Psalm 34:18",
        "verse_text": "The Lord is near to the brokenhearted and saves the crushed in spirit.",
        "prayer_text": (
            "God, loneliness can feel like a room full of people and an "
            "empty heart. But You promise to be near. Draw close to those "
            "who ache for connection today. Let them feel Your presence "
            "in the silence and know they are never truly alone."
        ),
        "theme_slug": "loneliness",
    },
]


def main() -> None:
    SAMPLES_DIR.mkdir(parents=True, exist_ok=True)

    for sample in SAMPLES:
        path = generate_single_overlay(
            verse_ref=sample["verse_ref"],
            verse_text=sample["verse_text"],
            prayer_text=sample["prayer_text"],
            theme_slug=sample["theme_slug"],
            chunk_index=0,
            hook_text=sample["hook_text"],
        )
        # Move to samples dir with descriptive name
        dest = SAMPLES_DIR / f"{sample['name']}.png"
        Path(path).rename(dest)
        print(f"  Saved: {dest}")

    print(f"\nDone! Review samples in {SAMPLES_DIR}/")


if __name__ == "__main__":
    main()
