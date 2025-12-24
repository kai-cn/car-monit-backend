package com.ruoyi.manager.domain.vo;

import com.baomidou.mybatisplus.annotation.TableField;
import com.ruoyi.common.annotation.Excel;
import lombok.Data;

/**
 * @BelongsProject: car-monit-backend-new
 * @BelongsPackage: com.ruoyi.manager.domain.vo
 * @Author: fengzhengqiang
 * @CreateTime: 2025-12-24  15:56
 * @Description: 日志查询
 * @Version: 1.0
 */
@Data
public class QueryLogVO {
	
	/** 用户名称 */
	private String userName;
	
	/** 模块菜单(1轨迹单2门架拍识3门架交易流水) */
	private String modelType;
	
	/** 模块功能(1查看2导出) */
	private String menuPoint;
	
	// 时间查询 :入口时间
	@TableField(exist = false)
	private String applyTime1;
	
	
	@TableField(exist = false)
	private String applyTime2;
}
