================================
PyModbus - A Python Modbus Stack
================================
=================
Making a release.
=================

------------------------------------------------------------
Prepare/make release on dev.
------------------------------------------------------------
* Make pull request "prepare v3.7.x", with the following:
   * Update pymodbus/__init__.py with version number (__version__ X.Y.Zpre)
   * Update README.rst "Supported versions"
   * Control / Update API_changes.rst
   * Update CHANGELOG.rst
      * Add commits from last release, but selectively !
        git log --oneline v3.7.0..HEAD > commit.log
        git log --pretty="%an" v3.7.0..HEAD | sort -uf > authors.log
        update AUTHORS.rst and CHANGELOG.rst
        cd doc; ./build_html
   * rm -rf build/* dist/*
   * python3 -m build
   * twine check dist/*
   * Commit, push and merge.
   * Wait for CI to complete
   * git pull
* Checkout master locally
   * git merge dev
   * git push
   * git branch -D master
   * wait for CI to complete on all branches
* On github "prepare release"
   * Create tag e.g. v3.7.0dev0
   * Title "pymodbus v3.7.0dev0"
   * do NOT generate release notes, but copy from CHANGELOG.rst
   * make release (remember to mark pre-release if so)
* on local repo
   * git pull, check release tag is pulled
   * git checkout v3.7.0dev0
   * rm -rf build/* dist/*
   * python3 -m build
   * twine upload dist/*  (upload to pypi)
   * Double check Read me docs are updated
      * trigger build https://readthedocs.org/projects/pymodbus/builds/
   * Mark release as active in readthedocs.org
* Make an announcement in discussions.


------------------------------------------------------------
Prepare release on dev for new commits.
------------------------------------------------------------
* Make pull request "prepare dev", with the following:
   * Update pymodbus/__init__.py with version number (__version__ X.Y.Zpre)


------------------------------------------------------------
Architecture documentation.
------------------------------------------------------------
* install graphviz
* pyreverse -k -o jpg pymodbus
