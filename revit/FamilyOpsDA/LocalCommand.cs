using System.Windows.Forms;
using Autodesk.Revit.Attributes;
using Autodesk.Revit.DB;
using Autodesk.Revit.UI;
using DialogResult = System.Windows.Forms.DialogResult;

namespace FamilyOpsDA;

/// <summary>
/// One-click Revit button: pick JSON → pick template → save .rfa folder.
/// No coding required for the end user.
/// </summary>
[Transaction(TransactionMode.Manual)]
public class RunOpsCommand : IExternalCommand
{
    public Result Execute(ExternalCommandData commandData, ref string message, ElementSet elements)
    {
        try
        {
            string opsPath;
            using (var dlg = new OpenFileDialog
            {
                Title = "Select the instructions file (revit_ops.json)",
                Filter = "Instructions JSON|revit_ops.json;*.json|All files|*.*",
                CheckFileExists = true
            })
            {
                if (dlg.ShowDialog() != DialogResult.OK)
                    return Result.Cancelled;
                opsPath = dlg.FileName;
            }

            string templatePath;
            using (var dlg = new OpenFileDialog
            {
                Title = "Select a Revit family template (.rft)",
                Filter = "Revit family template|*.rft|All files|*.*",
                CheckFileExists = true
            })
            {
                // Helpful default search path when present
                var templates = @"C:\ProgramData\Autodesk";
                if (Directory.Exists(templates))
                    dlg.InitialDirectory = templates;
                if (dlg.ShowDialog() != DialogResult.OK)
                    return Result.Cancelled;
                templatePath = dlg.FileName;
            }

            string outputDir;
            using (var dlg = new FolderBrowserDialog
            {
                Description = "Choose where to save the new family (.rfa)",
                UseDescriptionForTitle = true
            })
            {
                dlg.SelectedPath = Path.GetDirectoryName(opsPath) ?? @"C:\Temp";
                if (dlg.ShowDialog() != DialogResult.OK)
                    return Result.Cancelled;
                outputDir = dlg.SelectedPath;
            }

            FamilyOpsApp.Run(
                commandData.Application.Application,
                opsPath,
                templatePath,
                outputDir);

            TaskDialog.Show(
                "Done",
                "Family created.\n\nLook in:\n" + outputDir +
                "\n\nOpen the .rfa file in Revit to review it.");
            return Result.Succeeded;
        }
        catch (Exception ex)
        {
            message = ex.Message;
            TaskDialog.Show("Could not create family", ex.Message);
            return Result.Failed;
        }
    }
}

public class LocalApp : IExternalApplication
{
    public Result OnStartup(UIControlledApplication application)
    {
        const string tab = "FamilyOps";
        try { application.CreateRibbonTab(tab); } catch { /* exists */ }
        var panel = application.CreateRibbonPanel(tab, "Substation");
        var asm = typeof(LocalApp).Assembly.Location;
        var btn = new PushButtonData(
            "RunOps",
            "Create family\nfrom JSON",
            asm,
            typeof(RunOpsCommand).FullName!)
        {
            ToolTip = "Pick revit_ops.json and a .rft template, then save a .rfa family."
        };
        panel.AddItem(btn);
        return Result.Succeeded;
    }

    public Result OnShutdown(UIControlledApplication application) => Result.Succeeded;
}
