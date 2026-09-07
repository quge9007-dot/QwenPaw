package com.qwenpaw.usermanagement.dao.mapper;

import com.qwenpaw.usermanagement.dao.entity.UserAttributeDO;
import org.apache.ibatis.annotations.Mapper;
import org.apache.ibatis.annotations.Param;
import java.util.List;

/**
 * 用户属性数据访问接口
 */
@Mapper
public interface UserAttributeMapper {

    int insert(UserAttributeDO record);

    int updateById(UserAttributeDO record);

    UserAttributeDO selectByUserIdAndKey(@Param("userId") String userId, @Param("attrKey") String attrKey);

    List<UserAttributeDO> selectByUserId(@Param("userId") String userId);
}
