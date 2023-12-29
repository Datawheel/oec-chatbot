import {
  Anchor, Stack, Text, Title,
} from "@mantine/core";

function ChatResults({chatResponse, source}) {
  return (
    <Stack mt="md">
      <Title order={5}>
        Q:
        {" "}
        {chatResponse.query.question}
        ?
      </Title>
      <Text fz="lg">
        A:
        {" "}
        {chatResponse.query.answer}
      </Text>
      <Text fs="italic" fz="md">
        Source:
        {" "}
        <Anchor href={source} target="_blank">
          Observatory of Economic Complexity
        </Anchor>
      </Text>
    </Stack>
  );
}

export default ChatResults;
