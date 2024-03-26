import Image from "next/image";
import {NextSeo} from "next-seo";
import {useRef, useState} from "react";
import {
  Container, Title, Stack,
} from "@mantine/core";
import Chatbot from "@/components/chat/Chatbot";
// import RelatedResults from "../../components/chat/RelatedResults";




export default function ChatPage() {
  // initialize required variables
  

  return (
    <>
      <NextSeo title="DataUSA Chat" />
      <Container size="xl" py="xl">
        <Stack justify="flex-start" mt="20px">
          <Image src="/logo-shadow.png" width={200} height={50} style={{display: "block", margin: "0 auto"}} />
          <Title
            align="center"
            c="white"
            display="block"
            mx="auto"
            mt="xl"
            size="md"
            w="fit-content"
            // sx={{backgroundClip: "text"}}
          >
            Welcome to DataUSA Chat
          </Title>
          </Stack>
      </Container>
      <Container>
        <Chatbot />
      </Container>
    </>
  );
}
