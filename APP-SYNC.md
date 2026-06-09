# Sync features with the iOS app

We're going to use AI to sync features between this app and the sibling iOS app. The iOS app code is in `../wikipedia-ios`.

We're going to create some structure first, then experiment with syncing workflows to see what works well.

- Create a sync branch. We'll be tracking history and adding tests in this branch to improve verification.
- Create a “sync doc” at `.aisync/SYNCPLAN.md`. List all commits from af457ff7ae through HEAD, and create a checklist table with each in SYNCPLAN.md. Include an abbreviated commit SHA, the date, the author, size, and a very short summary of the commit.

Our first experiment will be to go from commit to commit, do analysis, determine if iOS changes are needed, then plan and execute those changed. We'll expand on that plan later, but first do the listed prep work.