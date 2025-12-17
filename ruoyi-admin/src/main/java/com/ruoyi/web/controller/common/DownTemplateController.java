

package com.ruoyi.web.controller.common;

import cn.afterturn.easypoi.excel.ExcelExportUtil;
import cn.afterturn.easypoi.excel.entity.TemplateExportParams;
import com.ruoyi.common.core.domain.AjaxResult;
import io.swagger.annotations.Api;
import io.swagger.annotations.ApiOperation;
import org.apache.poi.ss.usermodel.Workbook;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

import javax.servlet.http.HttpServletResponse;
import java.io.OutputStream;
import java.util.HashMap;


/**
 * 数据权限部门
 *
 * @author bim code generator
 * @date 2020-11-30 10:55:39
 */
@RestController
@RequestMapping("/downTemplate")
@Api(value = "downTemplate", tags = "模板下载")
public class DownTemplateController {


	/**
	 * 通过type下载模板
	 *
	 * @param type id
	 * @return R
	 */
	@ApiOperation(value = "通过type下载模板", notes = "通过type下载模板")
	@GetMapping("/{type}")
	public AjaxResult downExcel(@PathVariable("type") String type, HttpServletResponse response) {
		String url = "templates/down";
		if (type.equals("goodsFkApplyDetail")) {
			url = url + "/importGoodsFkApplyDetail.xlsx";
		}
		else if (type.equals("goodsRkApplyDetail")) {
			url = url + "/importGoodsRkApplyDetail.xlsx";
		}
		else if (type.equals("planListDetail")) {
			url = url + "/importPlanListDetail.xlsx";
		}
		else if (type.equals("importPsbz")) {
			url = url + "/importPsbz.xlsx";
		} else if ("importSupplierAnnualScore".equals(type)) {
			// 供应商年度评分导入模板
			url = url + "/importSupplierAnnualScore.xlsx";
		} else if ("carinfo".equals(type)) {
			// 车辆导入
			url = url + "/importCar.xlsx";
		} else if ("carExcept".equals(type)) {
			// 车辆追缴导入
			url = url + "/importCarExcept.xlsx";
		}

		try {
			TemplateExportParams params = new TemplateExportParams(url,true);
			Workbook workbook = ExcelExportUtil.exportExcel(params, new HashMap<String, Object>());
			response.setContentType("application/octet-stream;charset=UTF-8");
			response.setHeader("Content-Disposition", "attachment");
			OutputStream outs = response.getOutputStream();
			workbook.write(outs);
			outs.flush();
			outs.close();
		} catch (Exception e) {
			e.printStackTrace();
		}
		return null;
	}


}
