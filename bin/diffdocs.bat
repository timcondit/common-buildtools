::
:: A little differ-ent.
::
:: Description: Compares the documentation on Bigfoot with some destination,
:: usually the product source.  The point of this thing is to quickly check if
:: there are any new files to check into Subversion.
::
:: Parameters: a working copy in the form of
:: \\build5\Source\9.7\SP1\base-9.7.0100.13-r6449
::
:: It's having permission issues on copy, and it's just not worth the hassle.
:: Just take a diff, and copy them manually for now.
::

@echo OFF
if {%1}=={} (echo Error: need a destination) & (goto :EOF)
set SRC=\\Bigfoot\Engineering\Publications\From Truly to Tim\CurrentProjectFiles
set DST=%1\documentation
set DIFF=diff --brief

::
:: Copy everything.  Don't get clever, just get the files onto the build
:: machine.
::

:: EN CHM
%DIFF% "%SRC%\EN\CHM files\Administrator_Help.chm"      "%DST%\OnlineHelp\EN\Administrator_Help.chm"
%DIFF% "%SRC%\EN\CHM files\eLearning_Help.chm"          "%DST%\OnlineHelp\EN\eLearning_Help.chm"
%DIFF% "%SRC%\EN\CHM files\EWFM.chm"                    "%DST%\OnlineHelp\EN\EWFM.chm"
%DIFF% "%SRC%\EN\CHM files\QualityMonitoring_Help.chm"  "%DST%\OnlineHelp\EN\QualityMonitoring_Help.chm"
:: EN PDF
:: TODO rename QRS-CentricityAgentDesktop.pdf to "QRS - CentricityAgentDesktop.pdf"?
%DIFF% "%SRC%\EN\PDF files\QRS-CentricityAgentDesktop.pdf"  "%DST%\QuickReference\QRS - CentricityAgentDesktop.pdf"
%DIFF% "%SRC%\EN\PDF files\ReleaseNotes.pdf"                "%DST%\ReleaseNotes\ReleaseNotes.pdf"
:: TODO after 9.8 - uppercase administrator.pdf
%DIFF% "%SRC%\EN\PDF files\administrator.pdf"               "%DST%\UserGuides\administrator.pdf"
%DIFF% "%SRC%\EN\PDF files\AgentDesktop.pdf"                "%DST%\UserGuides\AgentDesktop.pdf"
%DIFF% "%SRC%\EN\PDF files\BizIntelPortal.pdf"              "%DST%\UserGuides\BizIntelPortal.pdf"
%DIFF% "%SRC%\EN\PDF files\eLearning.pdf"                   "%DST%\UserGuides\eLearning.pdf"
%DIFF% "%SRC%\EN\PDF files\EnvisionCallTaggingClient.pdf"   "%DST%\UserGuides\EnvisionCallTaggingClient.pdf"
%DIFF% "%SRC%\EN\PDF files\EWFM.pdf"                        "%DST%\UserGuides\EWFM.pdf"
%DIFF% "%SRC%\EN\PDF files\QualityMonitoring.pdf"           "%DST%\UserGuides\QualityMonitoring.pdf"
:: TODO after 9.8 - uppercase reporting.pdf
%DIFF% "%SRC%\EN\PDF files\reporting.pdf"                   "%DST%\UserGuides\reporting.pdf"
:: EN HTML
%DIFF% "%SRC%\EN\Webhelp files\Agent_Desktop_Webhelp.zip"               "%DST%\Webhelp\EN\Agent_Desktop_Webhelp.zip"
%DIFF% "%SRC%\EN\Webhelp files\BI_Webhelp.zip"                          "%DST%\Webhelp\EN\BI_Webhelp.zip"
%DIFF% "%SRC%\EN\Webhelp files\Centricity_Webhelp.zip"                  "%DST%\Webhelp\EN\Centricity_Webhelp.zip"
%DIFF% "%SRC%\EN\Webhelp files\Classic_reports_Webhelp.zip"             "%DST%\Webhelp\EN\Classic_reports_Webhelp.zip"
%DIFF% "%SRC%\EN\Webhelp files\Agent_Desktop_Centricity_Webhelp.zip"    "%DST%\Webhelp\EN\Agent_Desktop_Centricity_Webhelp.zip"

:: DE CHM
%DIFF% "%SRC%\DE\CHM files\Administrator_Help.chm"      "%DST%\OnlineHelp\DE\Administrator_Help.chm"
%DIFF% "%SRC%\DE\CHM files\eLearning_Help.chm"          "%DST%\OnlineHelp\DE\eLearning_Help.chm"
%DIFF% "%SRC%\DE\CHM files\QualityMonitoring_Help.chm"  "%DST%\OnlineHelp\DE\QualityMonitoring_Help.chm"
:: DE HTML
%DIFF% "%SRC%\DE\Webhelp files\Agent_Desktop_Webhelp.zip"   "%DST%\Webhelp\DE\Agent_Desktop_Webhelp.zip"
%DIFF% "%SRC%\DE\Webhelp files\Centricity_Webhelp.zip"      "%DST%\Webhelp\DE\Centricity_Webhelp.zip"
%DIFF% "%SRC%\DE\Webhelp files\Classic_reports_Webhelp.zip" "%DST%\Webhelp\DE\Classic_reports_Webhelp.zip"

:: ES CHM
%DIFF% "%SRC%\ES\CHM files\Administrator_Help.chm"      "%DST%\OnlineHelp\ES\Administrator_Help.chm"
%DIFF% "%SRC%\ES\CHM files\eLearning_Help.chm"          "%DST%\OnlineHelp\ES\eLearning_Help.chm"
%DIFF% "%SRC%\ES\CHM files\QualityMonitoring_Help.chm"  "%DST%\OnlineHelp\ES\QualityMonitoring_Help.chm"
:: ES HTML
%DIFF% "%SRC%\ES\Webhelp files\Agent_Desktop_Webhelp.zip"   "%DST%\Webhelp\ES\Agent_Desktop_Webhelp.zip"
%DIFF% "%SRC%\ES\Webhelp files\Centricity_Webhelp.zip"      "%DST%\Webhelp\ES\Centricity_Webhelp.zip"
%DIFF% "%SRC%\ES\Webhelp files\Classic_reports_Webhelp.zip" "%DST%\Webhelp\ES\Classic_reports_Webhelp.zip"


:: clean up
set SRC=
set DST=
set DIFF=

:EOF
