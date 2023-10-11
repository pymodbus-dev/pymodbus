================================
PyModbus - A Python Modbus Stack
================================
=================
Making a release.
=================

------------------------------------------------------------
Prepare/make release on dev.
------------------------------------------------------------
* Make pull request "prepare v3.5.x", with the following:
   * Update pymodbus/__init__.py with version number (__version__ X.Y.Zpre)
   * Update README.rst "Supported versions"
   * Control / Update API_changes.rst
   * Update CHANGELOG.rst
      * Add commits from last release, but selectively !
        git log --oneline v3.5.3..HEAD > commit.log
        git log --pretty="%an" v3.0.0..HEAD | sort -uf > authors.log
        update AUTHORS
        cd doc; ./build_html
   * Commit, push and merge.
* Checkout master locally
   * git merge dev
   * git push
   * git branch -D master
   * wait for CI to complete on all branches
* On github "prepare release"
   * Create tag e.g. v3.4.0dev0
   * Title "pymodbus v3.4.0dev0"
   * do NOT generate release notes, but copy from CHANGELOG.rst
   * make release (remember to mark pre-release if so)
* on local repo
   * git pull, check release tag is pulled
   * git checkout v3.0.0dev0
   * python3 setup.py sdist bdist_wheel
   * twine upload dist/*  (upload to pypi)
   * Double check Read me docs are updated
      * trigger build https://readthedocs.org/projects/pymodbus/builds/
* Make an announcement in discussions.


------------------------------------------------------------
Prepare release on dev for new commits.
------------------------------------------------------------
* Make pull request "prepare dev", with the following:
   * Update pymodbus/__init__.py with version number (__version__ X.Y.Zpre)
