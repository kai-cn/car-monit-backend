package com.ruoyi.web.controller.query;

import java.io.OutputStream;
import java.util.Arrays;
import java.util.HashMap;
import java.util.List;
import java.util.Map;

import cn.afterturn.easypoi.excel.ExcelExportUtil;
import cn.afterturn.easypoi.excel.entity.TemplateExportParams;
import com.ruoyi.common.utils.CommonUtil;
import com.ruoyi.common.utils.DateUtils;
import com.ruoyi.manager.domain.CarInfo;
import com.ruoyi.system.service.ISysDictDataService;
import org.apache.poi.ss.usermodel.Workbook;
import org.springframework.security.access.prepost.PreAuthorize;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.PutMapping;
import org.springframework.web.bind.annotation.DeleteMapping;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;
import com.ruoyi.common.annotation.Log;
import com.ruoyi.common.core.controller.BaseController;
import com.ruoyi.common.core.domain.AjaxResult;
import com.ruoyi.common.enums.BusinessType;
import com.ruoyi.query.domain.CarQueryLog;
import com.ruoyi.query.service.ICarQueryLogService;
import com.ruoyi.common.utils.poi.ExcelUtil;
import com.ruoyi.common.core.page.TableDataInfo;

import javax.servlet.http.HttpServletResponse;

/**
 * 查询日志Controller
 *
 * @author fzq
 * @date 2025-12-22
 */
@RestController
@RequestMapping("/query/querylog")
public class CarQueryLogController extends BaseController {

    @Autowired
    private ICarQueryLogService carQueryLogService;
    
    @Autowired
    private ISysDictDataService sysDictDataService;
    /**
     * 查询查询日志列表
     */
    @PreAuthorize("@ss.hasPermi('query:querylog:list')")
    @GetMapping("/list")
    public TableDataInfo list(CarQueryLog carQueryLog) {
        startPage();
        // carQueryLog.setTenantId(SecurityUtils.getTenantId()); // 查询我自己单位的租户
        List<CarQueryLog> list = carQueryLogService.selectCarQueryLogList(carQueryLog);
        return getDataTable(list);
    }
    /**
     * 获取查询日志详细信息
     */
    @GetMapping(value = "/{id}")
    public AjaxResult getInfo(@PathVariable("id") String id) {
        return AjaxResult.success(carQueryLogService.selectCarQueryLogById(id));
    }

    /**
     * 新增查询日志
     */
    @PreAuthorize("@ss.hasPermi('query:querylog:add')")
    @Log(title = "查询日志", businessType = BusinessType.INSERT)
    @PostMapping
    public AjaxResult add(@RequestBody CarQueryLog carQueryLog) {
        return carQueryLogService.saveCarQueryLog(carQueryLog);
    }

    /**
     * 修改查询日志
     */
    @PreAuthorize("@ss.hasPermi('query:querylog:edit')")
    @Log(title = "查询日志", businessType = BusinessType.UPDATE)
    @PutMapping
    public AjaxResult edit(@RequestBody CarQueryLog carQueryLog) {
        return carQueryLogService.saveCarQueryLog(carQueryLog);
    }

    /**
     * 删除查询日志
     */
    @PreAuthorize("@ss.hasPermi('query:querylog:remove')")
    @Log(title = "查询日志", businessType = BusinessType.DELETE)
    @DeleteMapping("/{ids}")
    public AjaxResult remove(@PathVariable String[] ids) {
        return carQueryLogService.deleteCarQueryLogByIds(ids);
    }
    
    
    @PreAuthorize("@ss.hasPermi('query:querylog:export')")
    @Log(title = "日志信息", businessType = BusinessType.EXPORT)
    @GetMapping("/export")
    public AjaxResult export(CarQueryLog carQueryLog, HttpServletResponse response) {
        List<CarQueryLog> list = carQueryLogService.selectCarQueryLogList(carQueryLog);
        
        // 模块菜单类型
        Map<String,String> modelTypeMap = sysDictDataService.selectDictDataMap("model_type");
        
        // 模块功能类型
        Map<String,String> menuPointMap = sysDictDataService.selectDictDataMap("menu_point");
        
        
        list.stream().forEach(dp -> {
            if (null != dp.getCreateTime()){
                dp.setCreateTime(dp.getCreateTime());
            }
            dp.setMenuPoint(CommonUtil.isNull(menuPointMap.get(dp.getMenuPoint())));
            dp.setModelType(CommonUtil.isNull(modelTypeMap.get(dp.getModelType())));
            
        });
        
        Map<String,Object> map = new HashMap<String,Object>();
        map.put("entitylist",list);
        try {
            String url = "templates/export/queryLog.xlsx";
            TemplateExportParams params = new TemplateExportParams(url);
            Workbook workbook = ExcelExportUtil.exportExcel(params, map);
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
