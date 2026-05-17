# Prevent pytest from collecting files inside fixture trees.
# These files are test *subjects* (source code that the extractor analyzes),
# not tests to execute.  The test_*.py naming is intentional — the extractor
# must handle test files as inputs — so we suppress collection here instead of
# renaming the fixture files.

collect_ignore_glob = ["**/test_*.py", "**/test_*.ts"]
