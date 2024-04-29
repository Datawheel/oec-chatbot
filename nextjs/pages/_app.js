import {MantineProvider} from "@mantine/core";
import {DefaultSeo} from "next-seo";

export default function App(props) {
  const {Component, pageProps} = props;

  return (
    <>
      <DefaultSeo title="OEC AI Chat" titleTemplate="%s | OEC AI Chat" />
      <MantineProvider
        withGlobalStyles
        
        theme={{
          /** Put your mantine theme override here */
          colorScheme: "dark",
        }}
      >
        <Component {...pageProps} />
      </MantineProvider>
    </>
  );
}
