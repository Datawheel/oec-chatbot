import axios from "axios";
import Image from "next/image";
import {NextSeo} from "next-seo";
import {useRef, useState} from "react";
import {IconSearch} from "@tabler/icons-react";
import {
  Container, TextInput, Title, Text, ActionIcon, Stack, Loader, Box,
} from "@mantine/core";

import ChatResults from "../components/chat/ChatResults";
import DataResults from "../components/chat/DataResults";
// import RelatedResults from "../../components/chat/RelatedResults";

function Loading({visible, text}) {
  if (!visible) return;
  // eslint-disable-next-line consistent-return
  return (
    <Box h="300px" my={90}>
      <Stack>
        <Text ta="center">{text}</Text>
        <Loader variant="bars" mx="auto" />
      </Stack>
    </Box>
  );
}

// eslint-disable-next-line prefer-destructuring
const NEXT_PUBLIC_CHAT_API = process.env.NEXT_PUBLIC_CHAT_API;
const {NEXT_PUBLIC_TESSERACT} = process.env;

export default function ChatPage() {
  // initialize required variables
  const [chatApiResponse, setchatApiResponse] = useState();
  const [chatDataResponse, setchatDataResponse] = useState();
  const [loading, setLoading] = useState(false);
  const [dataLoading, setdataLoading] = useState(false);
  const [searchText, setSearchText] = useState("How much did the CPI of fresh fruits change between 2019 and 2021?");
  const controller = useRef(null);

  // initialize required functions
  const handleSearch = () => {
    if (controller.current) {
      controller.current.abort();
    }
    controller.current = new AbortController();
    setLoading(true);

    const searchApi = (new URL(`/query/${searchText}`, NEXT_PUBLIC_CHAT_API)).href;
    axios.get(searchApi, {signal: controller.current.signal, timeout: 30000})
      .then((resp) => {
        setchatApiResponse(resp.data);
        handleData(resp.data.query.url);
        setLoading(false);
      })
      .catch((error) => {
        console.error("Error al realizar la consulta:", error);
        setLoading(false);
    });
  };

  const handleData = async (url) => {
    setdataLoading(true);

    await axios
      .get(url)
      .then((resp) => {
        setchatDataResponse(resp.data);
        setdataLoading(false);
      })
      .catch((error) => {
        console.error("Error al realizar la consulta:", error);
        setLoading(false);
    });
  };

  const searchAction = () => {
    handleSearch();
    setchatApiResponse(null);
    setchatDataResponse(null);
  };

  return (
    <>
      <NextSeo title="DataUSA Chat" />
      <Container size="xl" py="xl">
        <Stack justify="flex-start" mt="100px">
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
          <TextInput
            label={(
              <Text
                tt="uppercase"
                fw={400}
                size="md"
                ta="center"
              >
                Enter your question
              </Text>
            )}
            value={searchText}
            size="xl"
            onKeyDown={(e) => {
              if (e.key === "Enter") {
                searchAction();
              }
              // e.key;
            }}
            onChange={(e) => setSearchText(e.target.value)}
            rightSection={(
              <ActionIcon onClick={searchAction} variant="filled" color="oec-yellow" radius="xl">
                <IconSearch size="1rem" />
              </ActionIcon>
                      )}
          />
        </Stack>
        <Loading visible={loading} text="We're loading your result, please wait..." />
        {(chatApiResponse && !loading)
        && (
        <ChatResults
          chatResponse={chatApiResponse}
         // source={`${NEXT_PUBLIC_TESSERACT}${chatApiResponse.query.url}`}
          source="https://datausa.io/"
        />
        )}
        <Loading visible={dataLoading} text="We're loading your data results, please wait..." />
        {(chatDataResponse && !dataLoading) && <DataResults dataResponse={chatDataResponse} />}
        {/* {(chatApiResponse && chatDataResponse) && <RelatedResults context={chatApiResponse.context} neighbors={chatDataResponse.neighbors} />} */}
      </Container>
    </>
  );
}
