using System.Reflection;

var builder = WebApplication.CreateBuilder(args);
builder.Services.AddHealthChecks();

var app = builder.Build();
var commitSha = typeof(Program).Assembly.GetCustomAttributes<AssemblyMetadataAttribute>()
    .FirstOrDefault(attribute => attribute.Key == "CommitSha")?.Value;
if (string.IsNullOrWhiteSpace(commitSha))
{
    commitSha = "unknown";
}

app.MapGet("/", () => Results.Ok(new
{
    service = "ubuntu-apps-health-api",
    health = "/health"
}));

app.MapHealthChecks("/health");

app.MapGet("/version", (HttpResponse response) =>
{
    response.Headers.CacheControl = "no-store";
    return Results.Ok(new { commitSha });
});

app.Run();
