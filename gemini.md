# Goal 
Build a product that transcribes and summarises podcasts.

# Constraints
1. The code will be running on a local Windows machine.
2. Keep costs low. So run code locally where possible (e.g. for audio transcription, and using Gemini CLI for LLM-driven text summarisation), and use free tier google cloud services where we do need cloud hosting.

# Principles:
- Start small and build up in complexity over time.
- Write automated tests as we go.
- Make sure that all tests pass before we commit any code.
- Version control is important. The agent will handle git interactions with user oversight. Commit at every significant milestone.
- Fully complete each step in the 'Plan for iterative build' below before progressing to the next one.
- Maintain a log of our interactions over time. The agent will generate timestamped summary documents (which should pay particular attention to what went well and the areas where we had problems) in a 'gemini-interaction-summaries/' subfolder at significant milestones. These files should be added to .gitignore.
- For each stage of the 'Plan for iterative build' outlined below, the agent will explicitly highlight risky assumptions upfront. We will then work through the step, referencing these assumptions, and check our progress against them.

- **Commit Guidelines:**
    - **Frequency:** Commit frequently, at every significant milestone or logical unit of work.
    - **Atomicity:** Each commit should represent a single, atomic change.
    - **Messages:** Write clear, concise, and descriptive commit messages.
        - The first line (subject) should be 50 characters or less and summarize the change.
        - Leave a blank line after the subject.
        - The body (optional) should be wrapped at 72 characters and explain the *what* and *why* of the change.
        - **Mechanical Approach (for agent):** Due to CLI limitations, the agent will use a temporary `.txt` file to store the commit message and pass it to `git commit -F <filename>`.
    - **.gitignore:** Ensure `.gitignore` is properly configured to exclude generated files, temporary files, and sensitive information. Always run `git status` before committing to verify only intended files are staged.

# Plan for iterative build
1. Start by installing a CLI-based podcast downloading tool, and testing that it works.
2. Install the whisper transcription tool, and start transcribing podcast episodes.
3. Start summarising the content of the podcasts and writing them to a file locally.
4. Identify an email sending service that allows us to send via API, with a free tier for low usage volumes, or with a cheap paid offering (e.g. Amazon SES).