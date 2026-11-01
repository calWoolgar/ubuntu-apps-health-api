var builder = WebApplication.CreateBuilder(args);
builder.Services.AddHealthChecks();

var app = builder.Build();

app.MapGet("/", () => Results.Ok(new
{
    service = "ubuntu-apps-health-api",
    health = "/health"
}));

app.MapHealthChecks("/health");

app.Run();
