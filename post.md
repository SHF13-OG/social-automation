# Post Creation Checklist

Follow these steps in order for every new post.

## 1. Theme & Verse Selection
- Choose a theme from the database (`list-themes`) or discuss a topic
- Select an existing verse or add a new one to `bible_verses` table
- Confirm the hook question from the theme

## 2. Generate Prayer Text
- Use OpenAI with hook context
- Display the prayer text and word count for review

## 3. Review Before Proceeding
**STOP and present the following for approval:**

- **Verse reference** (e.g., Psalm 23:2-3)
- **Verse text** (full ESV quote)
- **Prayer text** (generated above)
- **Hook question** (from theme)
- **TikTok description/caption:**
  - Hook line
  - Verse quote with reference
  - Hashtags
- **Theme slug** and **theme name**

Wait for explicit approval or edits before continuing.

## 4. Generate Audio
- Specify provider (ElevenLabs or OpenAI TTS) and voice
- Default: OpenAI TTS with "ash" voice unless otherwise specified

## 5. Search & Download Footage
- Search Pexels for 2-3 clips matching the theme/mood
- Download portrait-orientation HD clips

## 6. Test Video (Optional)
**Ask: "Would you like to see a test video before creating the final?"**

If yes:
- Compose video to `media/videos/test-videos/`
- Wait for feedback and iterate on footage, voice, or overlay as needed
- Repeat until approved

If no:
- Proceed directly to final video

## 7. Compose Final Video
- Use approved audio, footage, and overlay settings
- Set `post_date` and `time_of_day` correctly
- Output to `media/videos/`

## 8. Save Database Records
- Save audio record to `audio_files`
- Save video record to `generated_videos`
- Create `lineup_entries` row with status `generated`
- Update `bible_verses.used_count` and `last_used_at`
- Set `generated_videos.created_at` to the target post date

## 9. Website Update
- Run `node scripts/bundle-db.js` to rebuild the bundled DB
- Verify "Today's Prayer" query returns the correct verse/prayer
- Deploy website

## 10. Deliver Final Output
Provide to user:
- Video file path
- Ready-to-use TikTok caption (hook + verse + hashtags)
- Confirmation that website is updated
