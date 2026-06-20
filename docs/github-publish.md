# GitHub Publish Checklist

1. Create a new repository on GitHub.
2. Add this project folder as the repo root.
3. Run:

```bash
git init
git add .
git commit -m "Initial release"
git branch -M main
git remote add origin <your-repo-url>
git push -u origin main
```

## Before publishing

- Add screenshots
- Test `python src/smartsort.py --dry-run`
- Test `python src/smartsort.py --gui`
- Commit and push to GitHub
- Create a `v1.0.0` release
