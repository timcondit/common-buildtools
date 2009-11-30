:: Set variables outside of SETLOCAL so that their values are "sticky", and do
:: not revert to their previous settings.
::
:: Late note: this may be okay inside the SETLOCAL when running the script the
:: "right way", where it actually kicks off the build, rather than just
:: parroting %BUILD_CALL% back to STDOUT.
::
:: TODO Consider using ANT_ARGS for the loggers and associated vars.  It won't
:: be super easy, since some of it will depend on generated values, but it
:: shouldn't be too bad.
::
:: TODO Move these into runbuild.py or a related command-generator utility.
:: Set them for *this* build only, with os.environ['JAVA_HOME']=r'C:\...',
:: etc.
set JAVA_HOME=C:\Program Files\Java\jdk1.6.0_14
set ANT_HOME=C:\Program Files\Ant\apache-ant-1.7.1
set ANT_OPTS=-Xmx1024m

@echo OFF
SETLOCAL

:: Check args, be verbose
if "%1" == "" (
    echo Usage: runbuild.bat current-buildnum previous-buildnum
    echo.
    echo runbuild.bat takes as input the current and previous
    echo build numbers, sets some environment variables, and runs
    echo the build.
    echo.
    echo CAUTION: This script does minimal error checking.  It is
    echo not intended to be run directly, but instead should
    echo always be called by runbuild.py.
    goto :EOF
    )

:: Current build
for /F "delims=. tokens=1-4" %%i in ("%1") do (
    if "%%l" == "" (
        echo Invalid build number [current]
        goto :EOF
    ) else (
        set MAJOR=%%i
        set MINOR=%%j
        set RELEASE=%%k
        set BUILD=%%l
        )
    )
set CURRENT_BUILD=%MAJOR%.%MINOR%.%RELEASE%.%BUILD%
echo [INFO] The current build: %CURRENT_BUILD%


:: Previous build
if "%2" NEQ "" (
    for /F "delims=. tokens=1-4" %%i in ("%2") do (
        if "%%l" == "" (
            echo Invalid build number [previous]
            goto :EOF
        ) else (
            set p_MAJOR=%%i
            set p_MINOR=%%j
            set p_RELEASE=%%k
            set p_BUILD=%%l
        )
    )
) else (
    if "%2" == "" (
        if "%BUILD%" == "0" (
            echo Error: A previous build number was not provided, and I
            echo cannot decrement 0
            goto :EOF
        )
        :: Previous build number was not provided, so decrement BUILD and
        :: assign it to p_BUILD.  All other assignments stay the same.
        set p_MAJOR=%MAJOR%
        set p_MINOR=%MINOR%
        set p_RELEASE=%RELEASE%
        set /a p_BUILD=%BUILD% - 1
    )
)
set PREVIOUS_BUILD=%p_MAJOR%.%p_MINOR%.%p_RELEASE%.%p_BUILD%
echo [INFO] The previous build: %PREVIOUS_BUILD%

:: This is bad.  I don't want to depend on positional arguments.
set SOURCE_URL=%3
echo [INFO] The source URL: %SOURCE_URL%


:: Set some options for the call to Ant.  See antsetup.bat for possibly
:: helpful comments that were removed from this section.
::
set MAIL_LOGGER=org.apache.tools.ant.listener.MailLogger
set XML_LOGGER=org.apache.tools.ant.XmlLogger
:: TODO ANT PROPERTY
set ANT_LOG_XSL_DIR=\\Bigfoot\Engineering\Projects\build\9.12\Initial\base\logs

:: I wanted to use this in build_%CURRENT_BUILD%.xml, but it's breaking the
:: build.
:: for /f "tokens=1-3 delims=:." %%a in ("%time%") do set TIMESTAMP=%%a%%b%%c

:: without Brockman :(
set BUILD_CALL=ant -DMAJOR=%MAJOR% -DMINOR=%MINOR% -DRELEASE=%RELEASE% -DBUILD=%BUILD% -Dp_MAJOR=%p_MAJOR% -Dp_MINOR=%p_MINOR% -Dp_RELEASE=%p_RELEASE% -Dp_BUILD=%p_BUILD% -DXmlLogger.file=%ANT_LOG_XSL_DIR%\build_%CURRENT_BUILD%.xml -listener %XML_LOGGER% -Dant.XmlLogger.stylesheet.uri=%ANT_LOG_XSL_DIR%\log.xsl -Durl.src=%SOURCE_URL%

:: DEBUG
echo %BUILD_CALL%

:: with Brockman :)  (includes multiple listeners!)
::set BUILD_CALL=ant -DMAJOR=%MAJOR% -DMINOR=%MINOR% -DRELEASE=%RELEASE% -DBUILD=%BUILD% -Dp_MAJOR=%p_MAJOR% -Dp_MINOR=%p_MINOR% -Dp_RELEASE=%p_RELEASE% -Dp_BUILD=%p_BUILD% -DXmlLogger.file=%ANT_LOG_XSL_DIR%\build_%CURRENT_BUILD%.xml -listener %XML_LOGGER% -Dant.XmlLogger.stylesheet.uri=%ANT_LOG_XSL_DIR%\log.xsl -Dconfigfile=brockman/config.xml -lib brockman/brockman.jar -listener org.buildmonitor.brockman.monitors.SimpleMonitor

if "%4" == "dry_run" (
    echo.
    echo Here is the Ant command based on provided input:
::    echo %BUILD_CALL% %4 %5 %6 %7 %8 %9
    echo %BUILD_CALL% %5 %6 %7 %8 %9
    echo.
    goto :EOF
)

if "%4" == "no_confirm" (
::    %BUILD_CALL% %4 %5 %6 %7 %8 %9
    %BUILD_CALL% %5 %6 %7 %8 %9
    goto :EOF
)

:: if {%3} == "None" (

echo Exiting.
goto :EOF

ENDLOCAL

