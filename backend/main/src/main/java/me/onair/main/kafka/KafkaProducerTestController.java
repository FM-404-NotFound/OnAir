package me.onair.main.kafka;

import java.text.SimpleDateFormat;
import java.util.Date;
import java.util.UUID;
import java.util.concurrent.CompletableFuture;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import me.onair.main.kafka.enums.Topics;
import me.onair.main.kafka.producer.KafkaProducer;
import org.springframework.kafka.core.KafkaTemplate;
import org.springframework.kafka.support.SendResult;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

@RestController
@RequestMapping("kafka")
@RequiredArgsConstructor
@Slf4j
public class KafkaProducerTestController {

    private final KafkaTemplate<String, String> kafkaTemplate;
    private final KafkaProducer kafkaProducer;

    @GetMapping("/publish/test-topic")
    public CompletableFuture<String> publishToTestTopic() {
        String message = createMessage();

        return sendMessageToKafka(message);
    }

    @PostMapping("/publish/media-topic/{channelName}")
    public CompletableFuture<String> publishToMediaTopicTestTest(
        @PathVariable String channelName, @RequestBody String message) {

        return kafkaProducer.sendMessageToKafka(
            Topics.MEDIA,
            channelName,
            message
        );
    }

    @GetMapping("/publish/channel-close-topic/{channelName}")
    public CompletableFuture<String> publishToChannelCloseTopicTestTest(@PathVariable String channelName) {

        return kafkaProducer.sendMessageToKafka(
            Topics.CHANNEL_CLOSE,
            channelName,
            "{\"content\": \"please close the channel\"}"
        );
    }

    private String createMessage() {
        String timeStamp = new SimpleDateFormat("yyyy-MM-dd HH:mm:ss").format(new Date());
        String uuid = UUID.randomUUID().toString().substring(0, 6); // UUID의 앞 6자리 추출
        return "Test Data: " + timeStamp + " " + uuid;
    }

    private CompletableFuture<String> sendMessageToKafka(String message) {
        CompletableFuture<SendResult<String, String>> future = kafkaTemplate.send(Topics.TEST.getName(), "key-1",
                message);

        return future.thenApply(result -> {
            log.info("레코드 전송 성공 = [{}] with offset=[{}]", message, result.getRecordMetadata().offset());
            return "success";
        }).exceptionally(ex -> {
            log.error("레코드 보낼 수 없음=[{}] due to : {}", message, ex.getMessage());
            return "fail";
        });
    }
}
