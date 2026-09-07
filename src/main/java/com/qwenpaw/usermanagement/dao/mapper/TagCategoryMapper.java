package com.qwenpaw.usermanagement.dao.mapper;

import com.qwenpaw.usermanagement.dao.entity.TagCategoryDO;
import org.apache.ibatis.annotations.Mapper;
import org.apache.ibatis.annotations.Param;
import java.util.List;

/**
 * 标签分类数据访问接口
 */
@Mapper
public interface TagCategoryMapper {

    int insert(TagCategoryDO record);

    int updateById(TagCategoryDO record);

    int deleteById(@Param("categoryId") String categoryId);

    TagCategoryDO selectById(@Param("categoryId") String categoryId);

    List<TagCategoryDO> selectAll();

    List<TagCategoryDO> selectByParentId(@Param("parentId") Long parentId);
}
