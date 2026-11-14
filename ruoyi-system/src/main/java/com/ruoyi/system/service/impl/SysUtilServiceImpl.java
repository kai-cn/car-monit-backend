package com.ruoyi.system.service.impl;

import java.text.SimpleDateFormat;
import java.util.Collection;
import java.util.Date;
import java.util.List;
import jakarta.annotation.PostConstruct;

import com.ruoyi.system.domain.SysUtil;
import com.ruoyi.system.mapper.SysUtilMapper;
import com.ruoyi.system.service.ISysUtilService;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.stereotype.Service;
import com.ruoyi.common.annotation.DataSource;
import com.ruoyi.common.constant.Constants;
import com.ruoyi.common.constant.UserConstants;
import com.ruoyi.common.core.redis.RedisCache;
import com.ruoyi.common.core.text.Convert;
import com.ruoyi.common.enums.DataSourceType;
import com.ruoyi.common.exception.CustomException;
import com.ruoyi.common.utils.StringUtils;
import com.ruoyi.system.domain.SysConfig;
import com.ruoyi.system.mapper.SysConfigMapper;
import com.ruoyi.system.service.ISysConfigService;

/**
 * 参数配置 服务层实现
 * 
 * @author ruoyi
 */
@Service
public class SysUtilServiceImpl implements ISysUtilService
{
    @Autowired
    private SysUtilMapper sysUtilMapper;
    @Override
    public String getBussCode(String bussType) {
        SysUtil bo = new SysUtil();
        // 当天时间
        String curDate = new SimpleDateFormat("yyyyMMdd").format(new Date());
        String tbsName = "";
        String billNo = "";
        String queryCondtion = "";
        if (bussType.equals("RK")) {
            // 入库单
            bussType = "RK";
            tbsName = "goods_rk_apply";
            billNo = bussType + curDate;
            queryCondtion = " t.buss_code like concat('" + billNo + "','%')";
        } else if (bussType.equals("CK")) {
            // 出库单
            bussType = "CK";
            tbsName = "goods_ck_apply";
            billNo = bussType + curDate;
            queryCondtion = " t.buss_code like concat('" + billNo + "','%')";
        }

        String bussCode = "";
        if (!tbsName.equals("")) {
            bo.setTbsName(tbsName); // 表格
            bo.setQueryCondtion(queryCondtion); //条件
            int countNum = sysUtilMapper.getBussCode(bo).getCountNum();
            if (countNum < 9) {
                bussCode = billNo + "00" + (countNum + 1);
            } else if (countNum < 99) {
                bussCode = billNo + "0" + (countNum + 1);
            } else {
                bussCode = billNo + "" + (countNum + 1);
            }
        }
        return bussCode;
    }
}
