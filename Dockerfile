FROM mcr.microsoft.com/dotnet/sdk:10.0-alpine AS build
WORKDIR /src
COPY src/HealthApi/HealthApi.csproj src/HealthApi/
RUN dotnet restore src/HealthApi/HealthApi.csproj
COPY src/HealthApi/ src/HealthApi/
ARG COMMIT_SHA=unknown
RUN dotnet publish src/HealthApi/HealthApi.csproj \
    --configuration Release --no-restore --output /app/publish \
    /p:UseAppHost=false /p:SourceRevisionId="$COMMIT_SHA"

FROM mcr.microsoft.com/dotnet/aspnet:10.0-alpine AS runtime
WORKDIR /app
ENV ASPNETCORE_HTTP_PORTS=8080
ARG COMMIT_SHA=unknown
LABEL org.opencontainers.image.revision=$COMMIT_SHA
COPY --from=build /app/publish .
USER $APP_UID
EXPOSE 8080
HEALTHCHECK --interval=30s --timeout=3s --start-period=10s --retries=3 \
    CMD wget -q -O /dev/null http://127.0.0.1:8080/health || exit 1
ENTRYPOINT ["dotnet", "HealthApi.dll"]
