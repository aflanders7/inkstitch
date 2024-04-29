---
title: "Contribute Code"
permalink: /developers/inkstitch/contribute-code/
excerpt: "Guide for how to contribute code to GitHub."
last_modified_at: 2024-04-28
toc: true 
---
This guide will walk you through how to make a contribution to the Ink/Stitch project on GitHub.

## Fork the Repository

To fork the repository, navigate to the Ink/Stitch project on GitHub and click "Fork" in the upper right corner of the page. Forking creates a personal copy of the repository. 
![Add python to path](/assets/images/developers/contribute-code/Fork.png)

## Clone the Repository

Clone the repository to your local computer via the terminal. 

```
https://github.com/your-username/inkstitch.git
```

## Create a New Branch

Create a new branch to isolate your changes. The following command creates and switches to a new branch. You can now make changes to the code.

```
git checkout -b username/your-new-feature
```

## Commit and Push Changes to GitHub

After making your desired changes, you need to commit your changes. Add a breif message describing the changes that you made. Then push those changes
to your forked repository on GitHub.

* This command adds all files to the commit:
  ```
  git add .
  ```

* Commit your changes with a message describing your changes:
  ```
  git commit -m "Your commit message here"
  ```

* If you do not know your branch name, the following command will show your current branch in green with an asterisk:
  ```
  git branch
  ```

* Push the changes to the remote repository using your branch name. If you have previously pushed changes from this branch, you can simply run 
`git push` to push your commits.
  ```
  git push -u origin branch-name
  ```

## Create a Pull Request

Pull requests allow the project maintainers to review and provide feedback on your proposed changes. To create a pull request, navigate to your
forked repository on GitHub. Select the branch that you were working on.
![Add python to path](/assets/images/developers/contribute-code/Branches.png)

At the top of the page you will see a notification to compare & pull request. Click the green button to create your pull request. 
![Add python to path](/assets/images/developers/contribute-code/Pull-Request.png)

Add a title and description that describes the changes you have made. Make sure that `Allow edits by maintainers` is selected. Then click the green button the create the pull request. This pull request will be visible in the pull requests tab of the main Ink/Stitch GitHub repository. Project maintainers will review your changes and either request changes or merge your changes into the main project.

