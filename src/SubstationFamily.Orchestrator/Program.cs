using System.Diagnostics;
using System.Text.Json;

var builder = WebApplication.CreateBuilder(args);
var app = builder.Build();

var repoRoot = FindRepoRoot();
var jobs = Path.Combine(repoRoot, "output");
Directory.CreateDirectory(jobs);

app.MapGet("/", () => Results.Ok(new
{
    service = "SubstationFamily.Orchestrator",
    pipeline = "PDF/CAD → RAG → Family Plan → Revit Ops → Validate",
    samples = new[] { "ABB_CB_245KV", "Siemens_XFMR_132KV", "GE_SD_145KV" }
}));

app.MapPost("/jobs", async (JobRequest req) =>
{
    if (string.IsNullOrWhiteSpace(req.PdfPath) || string.IsNullOrWhiteSpace(req.CadPath))
        return Results.BadRequest(new { error = "pdfPath and cadPath are required" });

    var jobId = string.IsNullOrWhiteSpace(req.JobId)
        ? $"job_{DateTime.UtcNow:yyyyMMdd_HHmmss}"
        : req.JobId!;
    var outDir = Path.Combine(jobs, jobId);
    Directory.CreateDirectory(outDir);

    var python = Path.Combine(repoRoot, "python");
    var psi = new ProcessStartInfo
    {
        FileName = "python3",
        WorkingDirectory = python,
        RedirectStandardOutput = true,
        RedirectStandardError = true,
    };
    psi.ArgumentList.Add("-m");
    psi.ArgumentList.Add("pipeline.run_job");
    psi.ArgumentList.Add("--pdf");
    psi.ArgumentList.Add(Path.GetFullPath(req.PdfPath, repoRoot));
    psi.ArgumentList.Add("--cad");
    psi.ArgumentList.Add(Path.GetFullPath(req.CadPath, repoRoot));
    psi.ArgumentList.Add("--out");
    psi.ArgumentList.Add(outDir);

    using var proc = Process.Start(psi) ?? throw new InvalidOperationException("Failed to start python");
    var stdout = await proc.StandardOutput.ReadToEndAsync();
    var stderr = await proc.StandardError.ReadToEndAsync();
    await proc.WaitForExitAsync();

    var validationPath = Path.Combine(outDir, "validation_report.json");
    object? validation = null;
    if (File.Exists(validationPath))
        validation = JsonSerializer.Deserialize<object>(await File.ReadAllTextAsync(validationPath));

    return Results.Json(new
    {
        jobId,
        exitCode = proc.ExitCode,
        stdout,
        stderr,
        outputDir = outDir,
        validation
    });
});

app.MapGet("/jobs/{jobId}", (string jobId) =>
{
    var dir = Path.Combine(jobs, jobId);
    if (!Directory.Exists(dir)) return Results.NotFound();
    var files = Directory.GetFiles(dir).Select(Path.GetFileName).ToArray();
    return Results.Ok(new { jobId, files });
});

app.Run();

static string FindRepoRoot()
{
    var dir = new DirectoryInfo(AppContext.BaseDirectory);
    while (dir is not null)
    {
        if (File.Exists(Path.Combine(dir.FullName, "README.md")) &&
            Directory.Exists(Path.Combine(dir.FullName, "python")))
            return dir.FullName;
        dir = dir.Parent;
    }
    return Directory.GetCurrentDirectory();
}

public record JobRequest(string PdfPath, string CadPath, string? JobId = null);
