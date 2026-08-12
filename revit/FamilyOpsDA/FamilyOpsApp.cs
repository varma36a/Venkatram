using Autodesk.Revit.ApplicationServices;
using Autodesk.Revit.DB;
using DesignAutomationFramework;
using Newtonsoft.Json.Linq;

namespace FamilyOpsDA;

/// <summary>
/// Design Automation for Revit entrypoint.
/// Reads revit_ops.json, builds a parametric box family, writes result.rfa.
/// </summary>
public class FamilyOpsApp : IExternalDBApplication
{
    public ExternalDBApplicationResult OnStartup(ControlledApplication app)
    {
        DesignAutomationBridge.DesignAutomationReadyEvent += OnDesignAutomationReady;
        return ExternalDBApplicationResult.Succeeded;
    }

    public ExternalDBApplicationResult OnShutdown(ControlledApplication app)
    {
        return ExternalDBApplicationResult.Succeeded;
    }

    private void OnDesignAutomationReady(object? sender, DesignAutomationReadyEventArgs e)
    {
        e.Succeeded = false;
        try
        {
            Run(e.DesignAutomationData.RevitApp);
            e.Succeeded = true;
        }
        catch (Exception ex)
        {
            Console.WriteLine($"FamilyOpsDA failed: {ex}");
            throw;
        }
    }

    internal static void Run(Application app)
    {
        var cwd = Directory.GetCurrentDirectory();
        var opsPath = Path.Combine(cwd, "revit_ops.json");
        if (!File.Exists(opsPath))
            throw new FileNotFoundException("revit_ops.json not found in working directory", opsPath);

        var root = JObject.Parse(File.ReadAllText(opsPath));
        var ops = (JArray?)root["ops"] ?? new JArray();

        string template = "template.rft";
        double widthMm = 1000, heightMm = 1000, depthMm = 1000;
        string familyFileName = "Equipment.rfa";
        var textParams = new Dictionary<string, string>();
        var numberParams = new Dictionary<string, double>();

        foreach (var token in ops)
        {
            var op = token.Value<string>("op");
            var args = token["args"] as JObject ?? new JObject();
            switch (op)
            {
                case "CreateFamilyDocument":
                    template = args.Value<string>("template") ?? template;
                    if (!template.EndsWith(".rft", StringComparison.OrdinalIgnoreCase) &&
                        !File.Exists(Path.Combine(cwd, template)))
                        template = "template.rft";
                    break;
                case "CreateExtrusion":
                    widthMm = args.Value<double?>("width") ?? widthMm;
                    heightMm = args.Value<double?>("height") ?? heightMm;
                    depthMm = args.Value<double?>("depth") ?? depthMm;
                    break;
                case "CreateParameter":
                {
                    var name = args.Value<string>("name") ?? "";
                    var type = args.Value<string>("type") ?? "Text";
                    if (type is "Length" or "Number")
                        numberParams[name] = args.Value<double?>("value") ?? 0;
                    else
                        textParams[name] = args.Value<string>("value") ?? args["value"]?.ToString() ?? "";
                    if (name == "Width") widthMm = numberParams[name];
                    if (name == "Height") heightMm = numberParams[name];
                    if (name == "Depth") depthMm = numberParams[name];
                    break;
                }
                case "SaveFamily":
                    familyFileName = Path.GetFileName(args.Value<string>("path") ?? familyFileName);
                    break;
            }
        }

        // Prefer uploaded template.rft in the DA working folder
        var templatePath = Path.Combine(cwd, "template.rft");
        if (!File.Exists(templatePath))
        {
            var alt = Path.Combine(cwd, template);
            if (File.Exists(alt)) templatePath = alt;
            else throw new FileNotFoundException(
                "Family template not found. Upload template.rft as the workitem input.", templatePath);
        }

        var famDoc = app.NewFamilyDocument(templatePath);
        try
        {
            using (var t = new Transaction(famDoc, "FamilyOpsDA build"))
            {
                t.Start();
                CreateBoxExtrusion(famDoc, widthMm, depthMm, heightMm);
                TrySetOrCreateParams(famDoc, numberParams, textParams);
                t.Commit();
            }

            var outPath = Path.Combine(cwd, "result.rfa");
            famDoc.SaveAs(outPath, new SaveAsOptions { OverwriteExistingFile = true });

            // Also copy to planned family name for convenience when downloaded
            var named = Path.Combine(cwd, familyFileName);
            if (!string.Equals(outPath, named, StringComparison.OrdinalIgnoreCase))
                File.Copy(outPath, named, overwrite: true);

            Console.WriteLine($"Saved {outPath} and {named}");
        }
        finally
        {
            famDoc.Close(false);
        }
    }

    static void CreateBoxExtrusion(Document famDoc, double widthMm, double depthMm, double heightMm)
    {
        // Revit internal units are feet
        double w = widthMm / 304.8;
        double d = depthMm / 304.8;
        double h = heightMm / 304.8;

        var profile = new CurveArrArray();
        var loop = new CurveArray();
        var p0 = new XYZ(-w / 2, -d / 2, 0);
        var p1 = new XYZ(w / 2, -d / 2, 0);
        var p2 = new XYZ(w / 2, d / 2, 0);
        var p3 = new XYZ(-w / 2, d / 2, 0);
        loop.Append(Line.CreateBound(p0, p1));
        loop.Append(Line.CreateBound(p1, p2));
        loop.Append(Line.CreateBound(p2, p3));
        loop.Append(Line.CreateBound(p3, p0));
        profile.Append(loop);

        var plane = Plane.CreateByNormalAndOrigin(XYZ.BasisZ, XYZ.Zero);
        var sketch = SketchPlane.Create(famDoc, plane);
        // Extrusion via FamilyItemFactory
        famDoc.FamilyCreate.NewExtrusion(true, profile, sketch, h);
    }

    static void TrySetOrCreateParams(
        Document famDoc,
        Dictionary<string, double> numbers,
        Dictionary<string, string> texts)
    {
        var fm = famDoc.FamilyManager;
        foreach (var (name, value) in numbers)
        {
            var existing = FindParam(fm, name);
            FamilyParameter p = existing ?? fm.AddParameter(
                name, GroupTypeId.IdentityData, SpecTypeId.Number, false);
            // Length-like names stored as mm numbers for identity; geometry already built
            fm.Set(p, value);
        }
        foreach (var (name, value) in texts)
        {
            var existing = FindParam(fm, name);
            FamilyParameter p = existing ?? fm.AddParameter(
                name, GroupTypeId.IdentityData, SpecTypeId.String.Text, false);
            fm.Set(p, value);
        }
    }

    static FamilyParameter? FindParam(FamilyManager fm, string name)
    {
        foreach (FamilyParameter p in fm.Parameters)
            if (p.Definition.Name == name) return p;
        return null;
    }
}
