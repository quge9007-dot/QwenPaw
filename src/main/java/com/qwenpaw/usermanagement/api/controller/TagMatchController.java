package com.qwenpaw.usermanagement.api.controller;

import com.qwenpaw.usermanagement.model.dto.MatchResultDTO;
import com.qwenpaw.usermanagement.model.request.TagMatchRequest;
import com.qwenpaw.usermanagement.service.TagMatchService;
import org.springframework.web.bind.annotation.*;

/**
 * 标签匹配控制器
 */
@RestController
@RequestMapping("/api/v1/match")
public class TagMatchController {

    private final TagMatchService tagMatchService;

    public TagMatchController(TagMatchService tagMatchService) {
        this.tagMatchService = tagMatchService;
    }

    @PostMapping
    public MatchResultDTO matchUsers(@RequestBody TagMatchRequest request) {
        return tagMatchService.matchUsersByTags(request);
    }
}
