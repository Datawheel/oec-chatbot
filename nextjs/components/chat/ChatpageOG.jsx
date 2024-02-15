import axios from "axios";
import {useRef, useState} from "react";
import {
     TextInput, Title, Text, ActionIcon, Stack, Loader, Box,
} from "@mantine/core";
import ChatResults from "./ChatResults";
import DataResults from "./DataResults";
import {IconSearch} from "@tabler/icons-react";

// eslint-disable-next-line prefer-destructuring
const NEXT_PUBLIC_CHAT_API = process.env.NEXT_PUBLIC_CHAT_API;


function Loading({visible, text}) {
    if (!visible) return;
    // eslint-disable-next-line consistent-return
    return (
      <Box h="100px" my={90}>
        <Stack>
          <Text ta="center">{text}</Text>
          <Loader variant="bars" mx="auto" />
        </Stack>
      </Box>
    );
  }


export default function ChatpageOG() {

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
        axios.get(searchApi, {signal: controller.current.signal})
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
            }}
            onChange={(e) => setSearchText(e.target.value)}
            rightSection={(
                <ActionIcon onClick={searchAction} variant="filled" color="oec-yellow" radius="xl">
                <IconSearch size="1rem" />
                </ActionIcon>
                    )}
        />
        <Loading visible={loading} text="We're loading your result, please wait..." />
        {
            (chatApiResponse && !loading)
            && (<ChatResults
                    chatResponse={chatApiResponse}
                    source="https://datausa.io/"
                />)
        }
        <Loading visible={dataLoading} text="We're loading your data results, please wait..." />
        {
            (chatDataResponse && !dataLoading) && <DataResults dataResponse={chatDataResponse} />
        }
        </>
    );
}