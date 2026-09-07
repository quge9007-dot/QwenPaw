package com.qwenpaw.usermanagement.dao.entity;

import com.qwenpaw.usermanagement.common.model.BaseEntity;

/**
 * 标签数据对象
 */
public class TagDO extends BaseEntity {

    private String tagId;
    private String tagName;
    private String tagCode;
    private String categoryId;
    private Long parentId;
    private Integer tagLevel;
    private Integer status;
    private Integer sortOrder;

    public String getTagId() {
        return tagId;
    }

    public void setTagId(String tagId) {
        this.tagId = tagId;
    }

    public String getTagName() {
        return tagName;
    }

    public void setTagName(String tagName) {
        this.tagName = tagName;
    }

    public String getTagCode() {
        return tagCode;
    }

    public void setTagCode(String tagCode) {
        this.tagCode = tagCode;
    }

    public String getCategoryId() {
        return categoryId;
    }

    public void setCategoryId(String categoryId) {
        this.categoryId = categoryId;
    }

    public Long getParentId() {
        return parentId;
    }

    public void setParentId(Long parentId) {
        this.parentId = parentId;
    }

    public Integer getTagLevel() {
        return tagLevel;
    }

    public void setTagLevel(Integer tagLevel) {
        this.tagLevel = tagLevel;
    }

    public Integer getStatus() {
        return status;
    }

    public void setStatus(Integer status) {
        this.status = status;
    }

    public Integer getSortOrder() {
        return sortOrder;
    }

    public void setSortOrder(Integer sortOrder) {
        this.sortOrder = sortOrder;
    }
}
