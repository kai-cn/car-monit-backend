// JAVA 对照: ruoyi-common/src/main/java/com/ruoyi/common/utils/poi/ExcelUtil.java:509-657,1383-1403
// JAVA 对照: ruoyi-quartz/src/main/java/com/ruoyi/quartz/domain/SysJob.java（@Excel 注解列）
// JAVA 对照: ruoyi-quartz/src/main/java/com/ruoyi/quartz/domain/SysJobLog.java（@Excel 注解列）
// 类/职责: 定时任务 / 调度日志的 Excel 导出
// 对应 Go 文件: internal/modules/quartz/excel.go
// 关键映射: ExcelUtil<SysJob>.exportExcel(list, "定时任务") -> 生成 xlsx 写入下载目录并返回文件名
//
// DIFF: Java 用 POI 逐单元格设置边框/颜色/提示；Go 用 excelize 生成等价内容，
// 仅保留表头加粗 + 底色 + 列宽，样式不是逐像素一致（数据与列顺序完全一致）。
// DIFF: 仍然写入 ruoyi.profile/download 并返回文件名（前端随后调用 /common/download 下载），
// 与 Java 行为一致；若 /common/download 尚未迁移，则只能拿到文件名。
package quartz

import (
	"context"
	"fmt"
	"os"
	"path/filepath"

	"github.com/google/uuid"
	"github.com/xuri/excelize/v2"

	"car-monit-go/internal/app"
	"car-monit-go/internal/excelx"
)

// exportSheet 描述一次导出的表头与行数据。
type exportSheet struct {
	name    string
	headers []string
	rows    [][]any
}

// ExportJobs 对应 SysJobController.export（ExcelUtil<SysJob>.exportExcel(list, "定时任务")）。
func (s *Service) ExportJobs(ctx context.Context, f JobFilter) (string, error) {
	rows, err := s.ListAllJobs(ctx, f)
	if err != nil {
		return "", err
	}
	data := make([][]any, 0, len(rows))
	for _, job := range rows {
		data = append(data, []any{
			job.JobID,
			job.JobName,
			job.JobGroup,
			job.InvokeTarget,
			job.CronExpression,
			convertByExp(job.MisfirePolicy, "0=默认,1=立即触发执行,2=触发一次执行,3=不触发立即执行"),
			convertByExp(job.Concurrent, "0=允许,1=禁止"),
			convertByExp(job.Status, "0=正常,1=暂停"),
		})
	}
	return writeExcel(s.a, exportSheet{
		name:    "定时任务",
		headers: []string{"任务序号", "任务名称", "任务组名", "调用目标字符串", "执行表达式 ", "计划策略 ", "并发执行", "任务状态"},
		rows:    data,
	})
}

// ExportJobLogs 对应 SysJobLogController.export（ExcelUtil<SysJobLog>.exportExcel(list, "调度日志")）。
func (s *Service) ExportJobLogs(ctx context.Context, f JobFilter) (string, error) {
	rows := make([]*SysJobLog, 0, 16)
	if err := s.jobLogQuery(ctx, f).Order("create_time desc").Find(&rows).Error; err != nil {
		return "", err
	}
	data := make([][]any, 0, len(rows))
	for _, log := range rows {
		data = append(data, []any{
			log.JobLogID,
			log.JobName,
			log.JobGroup,
			log.InvokeTarget,
			log.JobMessage,
			convertByExp(log.Status, "0=正常,1=失败"),
			log.ExceptionInfo,
		})
	}
	return writeExcel(s.a, exportSheet{
		name:    "调度日志",
		headers: []string{"日志序号", "任务名称", "任务组名", "调用目标字符串", "日志信息", "执行状态", "异常信息"},
		rows:    data,
	})
}

// writeExcel 生成 xlsx 并写入下载目录，返回文件名（编码规则同 ExcelUtil.encodingFilename：
// UUID + "_" + sheetName + ".xlsx"）。文件名全部由服务端生成，不含请求可控内容。
func writeExcel(a *app.App, sheet exportSheet) (string, error) {
	f := excelize.NewFile()
	defer func() { _ = f.Close() }()

	if err := f.SetSheetName("Sheet1", sheet.name); err != nil {
		return "", err
	}
	headerStyle, err := f.NewStyle(&excelize.Style{
		Font:      &excelize.Font{Bold: true},
		Alignment: &excelize.Alignment{Horizontal: "center", Vertical: "center"},
		Fill:      excelize.Fill{Type: "pattern", Pattern: 1, Color: []string{"#DDEBF7"}},
	})
	if err != nil {
		return "", err
	}

	for i, h := range sheet.headers {
		cell, err := excelize.CoordinatesToCellName(i+1, 1)
		if err != nil {
			return "", err
		}
		if err := f.SetCellValue(sheet.name, cell, h); err != nil {
			return "", err
		}
		if err := f.SetCellStyle(sheet.name, cell, cell, headerStyle); err != nil {
			return "", err
		}
	}
	for r, row := range sheet.rows {
		for c, v := range row {
			cell, err := excelize.CoordinatesToCellName(c+1, r+2)
			if err != nil {
				return "", err
			}
			if err := f.SetCellValue(sheet.name, cell, excelx.UtilCell(v)); err != nil {
				return "", err
			}
		}
	}
	lastCol, err := excelize.ColumnNumberToName(len(sheet.headers))
	if err != nil {
		return "", err
	}
	if err := f.SetColWidth(sheet.name, "A", lastCol, 20); err != nil {
		return "", err
	}

	filename := uuid.NewString() + "_" + sheet.name + ".xlsx"
	downloadPath := a.Cfg.RuoYi.DownloadPath()
	if err := os.MkdirAll(downloadPath, 0o755); err != nil {
		return "", fmt.Errorf("导出Excel失败，请联系网站管理员！: %w", err)
	}
	if err := f.SaveAs(filepath.Join(downloadPath, filename)); err != nil {
		return "", fmt.Errorf("导出Excel失败，请联系网站管理员！: %w", err)
	}
	return filename, nil
}

// convertByExp 对应 ExcelUtil.convertByExp：未命中返回空串（不是原值）。
func convertByExp(value, exp string) string {
	if exp == "" || value == "" {
		return value
	}
	return excelx.ConvertByExp(value, exp)
}
