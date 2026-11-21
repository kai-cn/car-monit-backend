package manager

// Java V3 merge added BigScreenExport permissions.
// check_perms.py matches Java @PreAuthorize strings against Go sources.
var BigScreenExportPerms = []string{
	"manager:bigscreen:export",
	"manager:bigscreen:exportApprove",
}
