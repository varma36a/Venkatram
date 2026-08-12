# Naming Conventions — Substation Revit Library

## Family file name
`<FamilyName>.rfa` must match the family `Name` parameter (without extension).

## Shared parameter file
Use `SUB_SharedParams.txt` groups:
- `SUB_Dimensions`
- `SUB_Electrical`
- `SUB_Identity`

## Type names
Prefer voltage-rated types: `245kV`, `132kV`, `145kV`.  
If multiple OEM variants share a family, use `245kV-ABB`, `245kV-SIEMENS`.

## Workset / library path
Publish path: `BIM_Library/Substation/Electrical/<TYPE>/`

## Forbidden
- Spaces in family names
- Vendor marketing slogans in family names
- Embedding project-specific tag numbers into the family name
