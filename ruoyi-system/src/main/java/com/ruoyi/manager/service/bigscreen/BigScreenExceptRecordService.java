package com.ruoyi.manager.service.bigscreen;

import com.ruoyi.common.utils.CommonUtil;
import com.ruoyi.manager.domain.CarConfimFree;
import com.ruoyi.manager.domain.CarExceptRecord;
import com.ruoyi.manager.domain.vo.bigscreen.CarIdCountVO;
import com.ruoyi.manager.service.ICarAduitFreeService;
import com.ruoyi.manager.service.ICarConfimFreeService;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.stereotype.Service;

import java.util.ArrayList;
import java.util.HashMap;
import java.util.LinkedHashSet;
import java.util.List;
import java.util.Map;
import java.util.Set;

/**
 * 异常流水行的批量补全：一次查询 orgId、一次聚合查询补缴状态，替代原有 2P+1 次查询。
 *
 * <p>orgId 匹配规则与原 SQL {@code find_in_set(except_ids, #{id})} 保持一致（保留历史语义，
 * 疑似参数顺序问题记录在 docs/decisions-v3.md）。</p>
 *
 * @author car-monit-backend-java-v3
 */
@Service
public class BigScreenExceptRecordService
{
    @Autowired
    private ICarConfimFreeService carConfimFreeService;

    @Autowired
    private ICarAduitFreeService carAduitFreeService;

    public void enrich(List<CarExceptRecord> rows)
    {
        if (rows == null || rows.isEmpty())
        {
            return;
        }
        List<String> carIds = new ArrayList<String>();
        Set<String> distinct = new LinkedHashSet<String>();
        for (CarExceptRecord row : rows)
        {
            if (CommonUtil.isNotBlank(row.getCarId()) && distinct.add(row.getCarId()))
            {
                carIds.add(row.getCarId());
            }
        }
        if (carIds.isEmpty())
        {
            return;
        }

        Map<String, List<CarConfimFree>> confimByCar = new HashMap<String, List<CarConfimFree>>();
        List<CarConfimFree> confimList = carConfimFreeService.selectOrgIdBatch(carIds);
        if (confimList != null)
        {
            for (CarConfimFree confim : confimList)
            {
                List<CarConfimFree> list = confimByCar.get(confim.getCarId());
                if (list == null)
                {
                    list = new ArrayList<CarConfimFree>();
                    confimByCar.put(confim.getCarId(), list);
                }
                list.add(confim);
            }
        }

        Map<String, Long> countByCar = new HashMap<String, Long>();
        List<CarIdCountVO> counts = carAduitFreeService.countByCarIds(carIds);
        if (counts != null)
        {
            for (CarIdCountVO count : counts)
            {
                countByCar.put(count.getCarId(), count.getCnt());
            }
        }

        for (CarExceptRecord row : rows)
        {
            row.setOrgId(resolveOrgId(confimByCar.get(row.getCarId()), row.getId()));
            Long count = countByCar.get(row.getCarId());
            if (count != null && count > 0L)
            {
                row.setSupplementaryStatus("1");
            }
        }
    }

    /**
     * 复刻原 SQL：select org_id ... where car_id = ? and find_in_set(except_ids, ?) > 0。
     */
    private String resolveOrgId(List<CarConfimFree> confims, String rowId)
    {
        if (confims == null || CommonUtil.isBlank(rowId))
        {
            return null;
        }
        for (CarConfimFree confim : confims)
        {
            String exceptIds = confim.getExceptIds();
            if (exceptIds == null)
            {
                continue;
            }
            if (rowId.contains(","))
            {
                for (String part : rowId.split(","))
                {
                    if (part.trim().equals(exceptIds))
                    {
                        return confim.getOrgId();
                    }
                }
            }
            else if (rowId.trim().equals(exceptIds))
            {
                return confim.getOrgId();
            }
        }
        return null;
    }
}
