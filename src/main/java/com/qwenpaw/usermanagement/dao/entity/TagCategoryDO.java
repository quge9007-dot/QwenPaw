package com.qwenpaw.usermanagement.dao.entity;

import com.qwenpaw.usermanagement.common.model.BaseEntity;

/**
 * 标签分类数据对象
 */
public class TagCategoryDO extends BaseEntity {

    private String categoryId;
    private String categoryName;
    private Long parentId;
    private Integer sortOrder;
    private Integer status;

    public String getCategoryId() {
        return categoryId;
    }

    public void setCategoryId(String categoryId) {
        this.categoryId = categoryId;
    }

    public String getCategoryName() {
        return categoryName;
    }

    public void setCategoryName(String categoryName) {
        this.categoryName = categoryName;
    }

    public Long getParentId() {
        return parentId;
    }

    public void setParentId(Long parentId) {
        this.parentId = parentId;
    }

    public Integer getSortOrder() {
        return sortOrder;
    }

    public void setSortOrder(Integer sortOrder) {
        this.sortOrder = sortOrder;
    }

    public Integer getStatus() {
        return status;
    }

    public void setStatus(Integer status) {
        this.status = status;
    }
}
