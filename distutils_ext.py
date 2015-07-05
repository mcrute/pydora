import os
import sys
from distutils import log
from distutils.cmd import Command
from distutils.errors import DistutilsError

class SimpleCommand(Command):

    user_options = []

    def initialize_options(self):
        pass

    def finalize_options(self):
        pass


class cover_test(SimpleCommand):

    description = "run unit tests with coverage"

    def run(self):
        from coverage import coverage

        cov = coverage(data_file=".coverage", branch=True,
                source=self.distribution.packages)
        cov.start()

        # Unittest calls exit. How naughty.
        try:
            self.run_command("test")
        except SystemExit:
            pass

        cov.stop()
        cov.xml_report(outfile="coverage.xml")



class check_style(SimpleCommand):

    description = "run PEP8 style validations"

    def run(self):
        from pep8 import StyleGuide

        self.run_command("egg_info")
        files = self.get_finalized_command("egg_info")

        report = StyleGuide().check_files([
            p for p in files.filelist.files if p.endswith(".py")])

        if report.total_errors:
            msg = "Found {} PEP8 violations".format(report.total_errors)
            raise DistutilsError(msg)
        else:
            log.info("No PEP8 violations found")
