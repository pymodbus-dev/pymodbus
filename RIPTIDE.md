Temporary fork of the pymodbus project until a fix for
[bashwork#101](https://github.com/bashwork/pymodbus/issues/101)
is published to [PyPI](http://pypi.org).

Create an internal version by:

0. Install the requirements to build the distribution:

        pip install -r requirements.txt

1. Edit `pymodbus/version.py` modifying the `pre=`
argument to `Version` to be a Riptide IO release candidate
("rc93101" being riptide rc1, "rc93012" being riptide rc2,
etc. That way our rc always "wins" the version comparison.)
2. Commit the changes.
3. Create an annotated tag:

        git tag -a -m "Riptide release-candidate 1: rc93101" rc93101

4. Push the changes, including the annotated tags:

        git push --follow-tags  # Do not use --tags!

5. Build and upload the version to the internal pip server:

        python setup.py sdist upload -r internal
