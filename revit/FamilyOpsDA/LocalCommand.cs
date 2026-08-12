using Autodesk.Revit.Attributes;
using Autodesk.Revit.DB;
using Autodesk.Revit.UI;

namespace FamilyOpsDA;

/// <summary>
/// Local Revit button for friends with desktop Revit.
/// Reads revit_ops.json + template.rft from a folder you pick / paste.
/// </summary>
[Transaction(TransactionMode.Manual)]
public class RunOpsCommand : IExternalCommand
{
    public Result Execute(ExternalCommandData commandData, ref string message, ElementSet elements)
    {
        try
        {
            var ui = new TaskDialog("FamilyOpsDA")
            {
                MainInstruction = "Generate .rfa from revit_ops.json",
                MainContent =
                    "Put revit_ops.json and template.rft in one folder.\n" +
                    "Default folder: C:\\Temp\\FamilyOpsJob\\\n\n" +
                    "Click Yes to run using that folder (create it first), " +
                    "or copy your job files there and retry.",
                CommonButtons = TaskDialogCommonButtons.Yes | TaskDialogCommonButtons.No
            };
            if (ui.Show() != TaskDialogResult.Yes)
                return Result.Cancelled;

            var folder = @"C:\Temp\FamilyOpsJob";
            if (!Directory.Exists(folder))
            {
                message = $"Folder not found: {folder}. Create it and copy revit_ops.json + template.rft there.";
                return Result.Failed;
            }

            var prev = Directory.GetCurrentDirectory();
            try
            {
                Directory.SetCurrentDirectory(folder);
                FamilyOpsApp.Run(commandData.Application.Application);
            }
            finally
            {
                Directory.SetCurrentDirectory(prev);
            }

            TaskDialog.Show("FamilyOpsDA", $"Done. Check {folder} for result.rfa / named .rfa");
            return Result.Succeeded;
        }
        catch (Exception ex)
        {
            message = ex.ToString();
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
        panel.AddItem(new PushButtonData(
            "RunOps",
            "Build .rfa\nfrom JSON",
            asm,
            typeof(RunOpsCommand).FullName));
        return Result.Succeeded;
    }

    public Result OnShutdown(UIControlledApplication application) => Result.Succeeded;
}
