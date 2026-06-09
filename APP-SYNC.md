# Sync features with the iOS app

We're going to use AI to sync features between this app and the sibling iOS app. The iOS app code is in `../wikipedia-ios`.

# Sync workflow

We're going to sync changes from the Android app to the iOS commit by commit. This will require creating a workflow that employs multiple agents for different phases.

For each Android app commit listed in '.aisync/SYNCPLAN.md', follow the following steps in order.

# Setup

Create branch in the iOS repo 'sync/[commit]'. The 'commit' is the commit SHA from the Android repo we are currently working on. We will be submitting a PR for each step, but they need to be in the same lineage, so each branch should have the changes from the previous.

# Maestro Test Evaluation

For each Android commit, deeply analyze the changes to determine if:
- Maestro tests can feasibly cover changes and features in the commit. Widgets and non-UI code may not be testable.
- Examine existing maestro tests to see if they cover the changes, or could be minimally extended to do so.
- Implement and run/verify those maestro tests for Android.

## Guidelines

Maestro tests should be written to `.maestro` in their respective repo. Screenshots should save to `.maestro/screenshots`.

Capture screenshots of every major state step in the maestro tests. We'll use these later as a form of comparison with the iOS implementation. Major states include button clicks, text entry, transitions, and any meaningful state/UI change. They do not need to capture overly precise changes. For example, we do not need to capture every character as it is entered into a text field.

Test all reasonably expected user flows. In cases where explicit states are required, use 'TestHooks' as described in '.maestro/MOCKING.md'.

# Change Plan

Commits will vary considerably in size and scope. Before implementing any changes, draft a checklist plan, phased if needed, to implement the changes. Save it to  '.aisync/plans' with the commit in the name. Ask the user questions if needed, but you do not need to present the final plan for approval.

# Plan Implementation

After the plan is drafted, agents should implement it. As the implementation progresses, be sure to update the plan doc to track, and commit after each work phase.

Change sets may be large, and intra-phase changes may not be reasonably testable. Do your best, but we will have a comprehensive verification step after the changes are applied.

Always use the source Android code as the authoritative code reference for a change. Avoid guessing when there is concrete code to reference.

# iOS Maestro Test Implementation

We will use Maestro on iOS to verify the changes. Evaluate the Maestro test changes made earlier in Android, and draft equivalent iOS Maestro tests in `[iOS repo]/.maestro`. Screenshots should be saved to `[iOS repo]/.maestro/screenshots` 

Each test must be run successfully to verify equivalent functionality.

# Screenshot comparison

After successfully completing the Maestro test verification, compare equivalent screenshots to verify reasonable UI fidelity. For each modified Maestro test, find the equivalent screenshots generated on Android and iOS. Compare them to ensure the same general features, text, and layout are present. This is not a deep test, but more of a sanity check that the UI is displaying as expected. To facilitate the outcome, resizing the images to a smaller and common width is advised. Use 360px, running system CLI tools. Copy the images to a temp folder before resizing. *DO NOT* modify the captured images that Maestro produced.

Modify the UI implementation on iOS for any major discrepancies, then rerun the associated Maestro tests, and continue. Don't repeat image comparisons for the same tests more than twice. Simply report the error in the plan document and move on.

# Wrap up

Draft a summary and append it to the commit change plan doc and update the checklist in '.aisync/SYNCPLAN.md'. Add/commit with a summary of the work performed. The use the GitHub cli tools to create a PR pointing back to main with the details of the changes from this session, and attach screenshots of any modified UI. Then print a summary to the user and ask if you should continue to the next task.