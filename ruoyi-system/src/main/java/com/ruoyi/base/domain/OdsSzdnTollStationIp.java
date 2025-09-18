package com.ruoyi.base.domain;

import com.baomidou.mybatisplus.annotation.IdType;
import com.baomidou.mybatisplus.annotation.TableId;
import com.baomidou.mybatisplus.annotation.TableName;
import com.ruoyi.common.core.domain.Custom;
import lombok.Data;
import lombok.EqualsAndHashCode;
import lombok.experimental.Accessors;

/**
 * 收费站ip对象 ods_szdn_toll_station_ip
 *
 * @author ruoyi
 * @date 2025-09-18
 */
@Data
@TableName("ods_szdn_toll_station_ip")
@Accessors(chain = true)
@EqualsAndHashCode(callSuper = false)
public class OdsSzdnTollStationIp implements Custom {

    @TableId(value = "id", type = IdType.ASSIGN_UUID)
    private Long id;

    private String tollCode;

    private String tollName;

    private String orgCode;

    private String ip;

    private String brand;


}
