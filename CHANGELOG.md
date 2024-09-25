# Changelog

All notable changes to [qstion](https://github.com/kajotgames/qstion) project will be documented in this file.

The format is based on [Keep a Changelog](http://keepachangelog.com/en/1.0.0/)
and this project adheres to [Semantic Versioning](http://semver.org/spec/v2.0.0.html).
## [1.1.7] - 2024-10-01

- added `QsRoot` method `pop` for removing node from tree - works like `dict.pop` method

## [1.1.5] - 2024-09-24

- added quoting to values which could represent decimal value when parsed with `parse_primitive` arg but need to be represented as strings (also applies for stringifying)

## [1.1.2] - 2024-09-09

- added utility methods to simplify array handling in `QsRoot` and `QsNode` classes

## [1.1.0] - 2024-09-04

- Refactored both `parser` and `stringifier` modules - better readability and maintainability
- Restructuralization of whole project - added more modules and divided code into smaller parts
- improved structures used for parsing and stringifying - Refactored `QsNode` and added `QsRoot` for better handling of nested objects
- parsing result can now be returned as dictionary or as `QsRoot` object for further manipulation
- added more functionality for handling tree objects - `QsRoot` and `QsNode` classes
- added some more keyword argument to configuration of both parser and stringifier for more flexibility

## [1.0.1] - 2024-03-06

- added option to parse directly from dictionary

## [1.0.0] - 2024-01-02

- version 1.0.0 released - first stable version
- fixed behavior of parsing when incoming data are `bytes` and delimiter is `str` (type incompatibility for regex module)

## [0.0.1] - 2023-11-06

- project created