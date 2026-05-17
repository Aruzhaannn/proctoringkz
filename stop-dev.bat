@echo off
title ProctorAI — Stop
color 0C

echo.
echo  Stopping all ProctorAI containers...
echo.

docker-compose down --remove-orphans

echo.
echo  OK — All containers stopped.
echo  Data in PostgreSQL and Redis is saved in Docker volumes.
echo.
echo  To fully clean up (delete DB and cache):
echo    docker-compose down -v
echo.
pause
