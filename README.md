- [Introduction](#introduction)
- [Requirements](#requirements)
- [Downloads](#downloads)
- [Installation - New Users](#installation---new-users)
- [Installation - Upgrading from a GAM version other than a prior version of GAMADV-X](#installation---upgrading-from-a-gam-version-other-than-a-prior-version-of-gamadv-x)
- [Installation - Upgrading from a prior version of GAMADV-X](#installation---upgrading-from-a-prior-version-of-gamadv-x)

# Introduction
GAMADV-X is a free, open source command line tool for Google G Suite Administrators to manage domain and user settings quickly and easily.

This page provides simple instructions for downloading, installing and starting to use GAMADV-X.

GAMADV-X requires G Suite for Business, Education, Non Profit, Partner or Government Edition. Google Apps Free Edition has limited API support and not all GAM commands work.

GAMADV-X is a rewrite/extension of Jay Lee's [GAM](https://github.com/jay0lee/GAM), without his efforts, this version wouldn't exist.

# Documentation
General GAM documentation is hosted in the [GitHub Wiki]. Documentation specifically for GAMADV-X is hosted in the [GitHub GAMADV-X Wiki] and in Gam*.txt files.

# Mailing List / Discussion group
The GAM mailing list / discussion group is hosted on [Google Groups].  You can join the list and interact via email, or just post from the web itself.

# Source Repository
The official GAMADV-X source repository is on [GitHub] in the master branch.

# Author
GAMADV-X is maintained by <a href="mailto:ross.scroggs@gmail.com">Ross Scroggs</a>.

# Requirements
To run all commands properly, GAMADV-X requires three things:
* An API project which identifies your install of GAMADV-X to Google and keeps track of API quotas.
* Authorization to act as your G Suite Administrator in order to perform management functions like add users, modify group settings and membership and pull domain reports.
* A special service account that is authorized to act on behalf of your users in order to modify user-specific settings and data such as Drive files, Calendars and Gmail messages and settings like signatures.

# Downloads
You can download the current GAMADV-X release from the [GitHub Releases](https://github.com/taers232c/GAMADV-X/releases) page. Choose one of the following:

* Single Executable Archive, Automatic, Linux/Mac OS/Google Cloud Shell
  - Start a terminal session.
  - `bash <(curl -s -S -L https://git.io/vMHsV) [-l] [-d <Path>]`
  - `-l` - Update to latest version, do not create project or authorizations
  - `-d <Path>` - Installation Path, defaults to $HOME/bin

* Single Executable Archive, Manual, Google Cloud Shell - `gamadv-x-4.wx.yz-debian-x86_64.tar.xz`
  - Download the archive, extract the contents into some directory.
  - Start a terminal session and cd to the install directory.

* Single Executable Archive, Manual, Linux - `gamadv-x-4.wx.yz-linux-x86_64.tar.xz, gamadv-x-4.wx.yz-debian-x86_64.tar.xz`
  - Download the archive, extract the contents into some directory.
  - Start a terminal session and cd to the install directory.

* Single Executable Archive, Manual, Mac OS - `gamadv-x-4.wx.yz-macos-10.10-11-x86_64.tar, gamadv-x-4.wx.yz-macos-10.12-13.tar`
  - Download the archive, extract the contents into some directory.
  - Start a terminal session and cd to the install directory.

* Single Executable Archive, Manual, Windows - `gamadv-x-4.wx.yz-windows-x64.zip, gamadv-x-4.wx.yz-windows.zip`
  - Download the archive, extract the contents into some directory.
  - Start a terminal session and cd to the install directory.

* Single Executable Installer, Manual, Windows - `gamadv-x-4.wx.yz-windows-x64.msi`
  - Download the installer and run it.
  - Start a Command Prompt/PowerShell session and cd to the install directory.

* Source, all platforms - Source code(zip), Source code(tar.gz)
  - Download the archive, extract the contents into some directory.
  - Start a terminal/Command Prompt/PowerShell session and cd to the install directory.

# Installation - New Users
For information about the GAMADV-X configuration file gam.cfg, see: https://github.com/taers232c/GAMADV-X/wiki/gam.cfg

Enter the following gam commands and follow instructions to create the necessary authorizations.
- Build gam.cfg: `gam config verify`
- Build GAM Project for authorization: `gam create project`
- Authorize Gam Client: `gam oauth create`
- Authorize Service Account: `gam user <EmailAddress> check serviceaccount`

# Installation - Upgrading from a GAM version other than a prior version of GAMADV-X
Please see  https://github.com/taers232c/GAMADV-X/wiki/How-to-Upgrade-from-Standard-GAM file for step-by-step instructions.

# Installation - Upgrading from a prior version of GAMADV-X
Read GamUpdate.txt

Download latest version, install over existing installation or in a parallel directory.

[GitHub Releases]: https://github.com/taers232c/GAMADV-X/releases
[GitHub]: https://github.com/taers232c/GAMADV-X/tree/master
[GitHub Wiki]: https://github.com/jay0lee/GAM/wiki/
[GitHub GAMADV-X Wiki]: https://github.com/taers232c/GAMADV-X/wiki/
[Google Groups]: http://groups.google.com/group/google-apps-manager
