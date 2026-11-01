# EADC automatic stats update

Upload the contents of this folder to the **root** of your existing EADC GitHub repository, preserving `.github/workflows/sync.yml` and `sync.py`. Do not upload the ZIP itself.

1. In GitHub Settings > Secrets and variables > Actions, verify `BALLCHASING_TOKEN` exists (do not expose its value).
2. In GitHub Actions, select **Sync EADC stats** and click **Run workflow**.
3. Check the job logs for success. It writes `stats.json` to your repository.
4. GitHub Pages will load `stats.json` on page refresh. Sync runs every six hours, and you can run it manually.

Notes: only uploaded replays can be imported; the existing site filters to the three Steam IDs on the same team. This is not live match streaming. The API may rate-limit or change response structure. Public GitHub Pages means your published replay statistics are public. Never commit your token.
