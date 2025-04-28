chcp 1251 >nul
SET PROJECT_NAME=check_tfoms_errors
FOR /F "tokens=* USEBACKQ" %%F IN (`python -c "from %PROJECT_NAME% import __version__; print(__version__)"`) DO (
    SET version=%%F
)
SET DIST_FOLDER=%PROJECT_NAME%_v%version%
RMDIR /Q /S %DIST_FOLDER%

pyinstaller --onefile --icon=logo128.ico --distpath=%DIST_FOLDER% %PROJECT_NAME%.py
COPY user_guide.pdf %DIST_FOLDER%\инструкция.pdf
COPY Q015.xml %DIST_FOLDER%\Q015.xml
COPY Q016.xml %DIST_FOLDER%\Q016.xml
COPY Q022.xml %DIST_FOLDER%\Q022.xml
COPY Q023.xml %DIST_FOLDER%\Q023.xml
MKDIR %DIST_FOLDER%\in
MKDIR %DIST_FOLDER%\out

DEL /Q /S %DIST_FOLDER%_dist.zip
rem "C:\Program Files\7-Zip\7z.exe" a %DIST_FOLDER%_dist.zip %DIST_FOLDER%
zip -r %DIST_FOLDER%_dist.zip %DIST_FOLDER%

DEL /Q /S *.spec
RMDIR /Q /S build
RMDIR /Q /S __pycache__
RMDIR /Q /S %DIST_FOLDER%