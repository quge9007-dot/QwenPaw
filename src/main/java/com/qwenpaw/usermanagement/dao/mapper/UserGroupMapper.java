package com.qwenpaw.usermanagement.dao.mapper;

import com.qwenpaw.usermanagement.dao.entity.UserGroupDO;
import org.apache.ibatis.annotations.Mapper;
import org.apache.ibatis.annotations.Param;
import java.util.List;

/**
 * 用户分群数据访问接口
 */
@Mapper
public interface UserGroupMapper {

    int insert(UserGroupDO record);

    int updateById(UserGroupDO record);

    int deleteById(@Param("groupId") String groupId);

    UserGroupDO selectById(@Param("groupId") String groupId);

    List<UserGroupDO> selectAll();

    List<UserGroupDO> selectByStatus(@Param("status") Integer status);
}
