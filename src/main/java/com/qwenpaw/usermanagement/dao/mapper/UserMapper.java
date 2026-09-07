package com.qwenpaw.usermanagement.dao.mapper;

import com.qwenpaw.usermanagement.dao.entity.UserDO;
import org.apache.ibatis.annotations.Mapper;
import org.apache.ibatis.annotations.Param;
import java.util.List;

/**
 * 用户数据访问接口
 */
@Mapper
public interface UserMapper {

    int insert(UserDO record);

    int updateById(UserDO record);

    int deleteById(@Param("userId") String userId);

    UserDO selectById(@Param("userId") String userId);

    List<UserDO> selectAll();

    List<UserDO> selectByStatus(@Param("status") Integer status);

    int countByStatus(@Param("status") Integer status);

    List<UserDO> selectByTagIds(@Param("tagIds") List<String> tagIds);
}
